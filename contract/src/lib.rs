//! # Pumpit Soroban Contract
//!
//! The contract allows to deposit some amount of token from one address to
//! the contract's address itself. It further allows another
//! account to claim its balance when a certain level is reach.
//!
//! This contract is to be used by the accompanying IOT code which runs on
//! a Raspberry Pi.
//!
//! This contracts is inspired by the *timelock* example:
//! https://github.com/stellar/soroban-examples/tree/main/timelock

#![no_std]

use soroban_sdk::{contract, contractimpl, contracttype, token, Address, BytesN, Env, Vec};

#[contracttype]
#[derive(Clone)]
enum AdminKey {
    Admin,  // Contract administrator
}

#[derive(Clone)]
#[contracttype]
pub enum DataKey {
    Init,  // A key to check if the contract was initialized or not
    Balance,  // Hold the claimable balance
}

#[derive(Clone)]
#[contracttype]
pub struct ClaimableBalance {
    pub token: Address,
    pub amount: i128,
    pub claimants: Vec<Address>,
    pub pumping_level_target: i128,
}

#[contract]
pub struct ClaimableBalanceContract;

#[contractimpl]
impl ClaimableBalanceContract {
    pub fn init(env: Env, admin: Address) {
        env.storage().instance().set(&AdminKey::Admin, &admin);
    }

    pub fn version() -> u32 {
        1
    }

    /// Deposit an `amount` of `token` to the contract's address.
    /// Tokens originate from the `from` address and they can be claimed by
    /// any of the `claimants` addresses if the `pumping_level_target` is
    /// satisfied.
    ///
    /// Note: `token` is a hash. The CLI can be used to get it's value on a
    /// given network:
    /// `soroban lab token id --asset native --network testnet`
    pub fn deposit(
        env: Env,
        from: Address,
        token: Address,
        amount: i128,
        claimants: Vec<Address>,
        pumping_level_target: i128,
    ) {
        // Make sure `from` address authorized the deposit call with all the
        // arguments.
        from.require_auth();

        if is_initialized(&env) {
            panic!("contract has been already initialized");
        }
        if claimants.len() > 20 {
            panic!("only 20 claimants can play");
        }

        // Transfer token from `from` to this contract address.
        token::Client::new(&env, &token).transfer(&from, &env.current_contract_address(), &amount);
        // Store all the necessary info to allow one of the claimants to claim it.
        env.storage().instance().set(
            &DataKey::Balance,
            &ClaimableBalance {
                token,
                amount,
                pumping_level_target,
                claimants,
            },
        );
        // Mark contract as initialized to prevent double-usage.
        env.storage().instance().set(&DataKey::Init, &());
    }

    pub fn claim(env: Env, claimant: Address, pumping_level: i128) {
        // Make sure claimant has authorized this call, which ensures their
        // identity.
        claimant.require_auth();

        if !is_initialized(&env) {
            panic!("contract has not been initialized");
        }

        // Just get the balance - if it's been claimed, this will simply panic
        // and terminate the contract execution.
        let claimable_balance: ClaimableBalance =
            env.storage().instance().get(&DataKey::Balance).unwrap();

        let claimants = &claimable_balance.claimants;
        if !claimants.contains(&claimant) {
            panic!("claimant is not allowed to claim this balance");
        }

        if pumping_level < claimable_balance.pumping_level_target {
            panic!("need to pump more!");
        }

        // Transfer the stored amount of token to claimant after passing
        // all the checks.
        token::Client::new(&env, &claimable_balance.token).transfer(
            &env.current_contract_address(),
            &claimant,
            &claimable_balance.amount,
        );
        // Reset the contract data
        reset(env)
    }

    /// Reset the contract by deleting the claimable balance info.
    /// You can lose the token!
    pub fn reset(env: Env) {
        let admin: Address = env.storage().instance().get(&AdminKey::Admin).unwrap();
        admin.require_auth();

        reset(env)
    }

    pub fn upgrade(env: Env, new_wasm_hash: BytesN<32>) {
        let admin: Address = env.storage().instance().get(&AdminKey::Admin).unwrap();
        admin.require_auth();

        env.deployer().update_current_contract_wasm(new_wasm_hash);
    }
}

// Helper functions
fn reset(env: Env) {
    env.storage().instance().remove(&DataKey::Balance);
    env.storage().instance().remove(&DataKey::Init);
}

fn is_initialized(env: &Env) -> bool {
    env.storage().instance().has(&DataKey::Init)
}
