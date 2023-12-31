.PHONY: help install prepare fmt clean build test build-release deploy contract_help contract_init contract_deposit contract_claim
.DEFAULT_GOAL := help
SHELL:=/bin/bash

# Add help text after each target name starting with '\#\#'
help:   ## show this help
	@echo -e "Help for this makefile\n"
	@echo "Possible commands are:"
	@grep -h "##" $(MAKEFILE_LIST) | grep -v grep | sed -e 's/\(.*\):.*##\(.*\)/    \1: \2/'

install:  ## install Rust and Soroban-CLI
	# install Rust
	curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh && \
	# install Soroban and config
	rustup target add wasm32-unknown-unknown && \
	cargo install --locked soroban-cli --features opt && \

prepare:  ## Generate identity and fund
	soroban config network add --global testnet \
  		--rpc-url https://soroban-testnet.stellar.org:443 \
  		--network-passphrase "Test SDF Network ; September 2015" && \
	# generate addresses and add funds
	soroban config identity generate grogu && \
	soroban config identity generate mando && \
	soroban config identity fund grogu --network testnet && \
	soroban config identity fund mando --network testnet && \
	mkdir -p .soroban

fmt:
	cargo fmt --all

clean:
	cargo clean

build:
	soroban contract build
	@ls -l target/wasm32-unknown-unknown/release/*.wasm

test: build
	cargo test

build-release: build
	soroban contract optimize --wasm target/wasm32-unknown-unknown/release/pumpit.wasm
	@ls -l target/wasm32-unknown-unknown/release/*.wasm

deploy: build-release  ## Deploy Soroban contract to testnet
	soroban contract deploy \
  		--wasm target/wasm32-unknown-unknown/release/pumpit.optimized.wasm \
  		--source mando \
  		--network testnet \
  		> .soroban/pumpit_id && \
  	cat .soroban/pumpit_id

contract_help:
	soroban contract invoke \
    	--source mando \
    	--network testnet \
    	--id $(shell cat .soroban/pumpit_id) \
    	-- \
    	--help

contract_init:  ## Initialise admin of the contract
	soroban contract invoke \
    	--source mando \
    	--network testnet \
    	--id $(shell cat .soroban/pumpit_id) \
    	-- \
    	init \
    	--admin $(shell soroban config identity address mando)

contract_version:
	soroban contract invoke \
    	--source mando \
    	--network testnet \
    	--id $(shell cat .soroban/pumpit_id) \
    	-- \
    	version

contract_upgrade:
	soroban contract invoke \
    	--source mando \
    	--network testnet \
    	--id $(shell cat .soroban/pumpit_id) \
    	-- \
    	upgrade \
		--new_wasm_hash $(shell soroban contract install --wasm target/wasm32-unknown-unknown/release/pumpit.optimized.wasm)

contract_reset:
	soroban contract invoke \
    	--source mando \
    	--network testnet \
    	--id $(shell cat .soroban/pumpit_id) \
    	-- \
    	reset

contract_deposit:  ## Deposit fund to the contract and set target
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

contract_claim:  ## Claim funds with a level
	soroban contract invoke \
    	--source grogu \
    	--network testnet \
    	--id $(shell cat .soroban/pumpit_id) \
    	-- \
    	claim \
    	--claimant $(shell soroban config identity address grogu) \
		--pumping_level 15
