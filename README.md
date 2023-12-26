# Pumpit

The goal of this project is to play with IOT and
[Soroban](https://soroban.stellar.org) - Stellar Smart Contract.

## Game Play

It's simple, the Smart Contract is initialised with a volume to pump and
multiple addresses each corresponding to a participant. All participants,
have their Raspberry Pi ready to pump, literally, and the first to reach the
pumping level would win and receive the funds.

If I am bored enough, I might make a UI for the Pi(s) so participants can
set their address and see their progress... Or better yet someone can make a PR ;)

## Raspberry Pi

One Raspberry Pi corresponds to one player. Once the Python service is
started, it will listen on a GPIO connected to the flow meter. After a given
volume is pumped, a RPC call to the Soroban contract will be made to claim
funds.

### Hardware

I am using a Raspberry Pi Zero 2 W. BOM:

- Raspberry Pi Zero 2 W
- Water flow meter (+1x 10K and +1x 20K ohm resistances: 5V to 3.3V on the GPIO)
- Button (+1x 220 ohm resistance)
- Green LED (+1x 220 ohm resistance)
- RED LED (+1x 220 ohm resistance)
- RGB LED (+3x 220 ohm resistance)

See `iot/pumpit.py` for details on which GPIO to connect, it's very
straightforward.

![Raspberry Pi diagram](doc/diagram.png)

### Python service

After a classical headless setup of the Raspberry Pi, install everything Python:
```bash
ssh grogu@pumpit -i .ssh/raspberrypi_zero
sudo apt-get install libopenblas-dev
cd iot
python -m venv venv
source venv/bin/activate
pip install .
```

And also everything needed to run the Soroban contract:

```bash
# install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh && \
# install Soroban and config
rustup target add wasm32-unknown-unknown && \
cargo install --locked soroban-cli --features opt && \
```

Then to run the game client (provided the contract is initialized, see bellow):

```bash
python pumpit.py
```

Behind the scene, it will invoke the contract once we reach the pumping
threshold.

## Soroban - Stellar Smart Contract

We define a Smart Contract that hold a claimable balance. When conditions are
met, the balance is transferred to a claimant.

*Note: all commands are listed in a convenient Makefile in the contract folder.*
### Setup
These steps are to be done on any machine, not the Pi(s).

Following the Soroban [doc](https://soroban.stellar.org/docs), we setup a
Soroban local environment and install all dependencies. 
```bash
cd contract
# install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
# install Soroban and config
rustup target add wasm32-unknown-unknown
cargo install --locked soroban-cli --features opt
```

We create two accounts on testnet and add some funds (in XLM).

```bash
soroban config network add --global testnet
	--rpc-url https://soroban-testnet.stellar.org:443
	--network-passphrase "Test SDF Network ; September 2015"
# generate addresses and add funds
soroban config identity generate grogu
soroban config identity generate mando
soroban config identity fund grogu --network testnet
soroban config identity fund mando --network testnet
mkdir -p .soroban
```

When doing operations on accounts (addresses), we can check the explorer:

https://testnet.steexp.com/account/

![Accounts on Stellar Explorer](doc/stellar_explorer_fund.png)

After our contract is written/tested/ready, we can build and upload it to
testnet:

```bash
soroban contract build
soroban contract optimize --wasm target/wasm32-unknown-unknown/release/pumpit.wasm
soroban contract deploy \
	--wasm target/wasm32-unknown-unknown/release/pumpit.optimized.wasm \
	--source mando \
	--network testnet \
	> .soroban/pumpit_id
```

This will build the WASM file, upload it to testnet and create the contract.
The last two operations are distinct transactions on the network, hence there
are 2 fees associated to it (at the time of writing, around 100k stroop.)

![Upload contract and see in Stellar Explorer](doc/stellar_explorer_contract_create.png)

Now we can interact with our contract!

### Interact with the contract

We can initialize the admin of the contract (useful to upgrade without
changing the ID/hash on client side):

```bash
soroban contract invoke \
	--source mando \
	--network testnet \
	--id $(shell cat .soroban/pumpit_id) \
	-- \
	init \
	--admin $(shell soroban config identity address mando)
```

Then we can transfer some funds on the contract which will be claimable. Let's
use 100 XLM from our user `mando`. Note that the unit on Soroban is Stroops
which means `100 XLM = 1.10e9 Stroops`. We also need a target for our pumping
level, let's say 10L:

```bash
soroban contract invoke \
	--source mando \
	--network testnet \
	--id $(shell cat .soroban/pumpit_id) \
	-- \
	deposit \
	--from $(shell soroban config identity address mando) \
	--token $(shell soroban lab token id --asset native --network testnet) \
	--amount 1000000000 \
	--claimants '{ "vec": [{ "address": "$(shell soroban config identity address grogu)" }] }' \
	--pumping_level_target 10
```

Note that to specify the token (XLM), we need to use its hash on the network. 

```bash
soroban lab token id --asset native --network testnet
# CDLZFC3SYJYDZT7K67VZ75HPJVIEUVNIXF47ZG2FB2RMQQVU2HHGCYSC  # may vary
```

![Deposit and see in Stellar Explorer](doc/stellar_explorer_deposit.png)

The contract is ready to be used! The following is done as part of the
game on the Raspberry Pi(s).

We try to claim funds by e.g. setting the current pumping level to 15L:

```bash
soroban contract invoke \
	--source grogu \
	--network testnet \
	--id $(shell cat .soroban/pumpit_id) \
	-- \
	claim \
	--claimant $(shell soroban config identity address grogu) \
	--pumping_level 15
```

Tada, it should say `in_successful_contract_call: true` and balances of the
contract and claimant have changed:

![Claim and see in Stellar Explorer](doc/stellar_explorer_claim.png)

Checking the balance shows that the address did receive the funds from the
claimable balance:
![Balance after claim and see in Stellar Explorer](doc/stellar_explorer_fund_after_claim.png)
