default: build

all: test

install:
	# install Rust
	curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh && \
	# install Soroban and config
	rustup target add wasm32-unknown-unknown && \
	cargo install --locked soroban-cli --features opt && \

prepare:
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

build-release:
	soroban contract optimize
	@ls -l target/wasm32-unknown-unknown/release/*.wasm

deploy: build-release
	soroban contract deploy \
  		--wasm target/wasm32-unknown-unknown/release/pumpit.wasm \
  		--source mando \
  		--network testnet \
  		> .soroban/pumpit_id && \
  	@cat .soroban/pumpit_id

contract_init:
	soroban contract invoke \
    	--source mando \
    	--network testnet \
    	--id $(shell cat .soroban/pumpit_id) \
    	-- \
    	deposit \
    	--from $(shell soroban config identity address mando) \
    	--token $(shell soroban lab token id --asset native --network testnet) \
    	--amount 100000000 \
    	--claimants '{ "vec": [{ "address": "$(shell soroban config identity address grogu)" }] }' \
    	--pumping_level_target 10

contract_claim:
	soroban contract invoke \
    	--source grogu \
    	--network testnet \
    	--id $(shell cat .soroban/pumpit_id) \
    	-- \
    	claim \
    	--claimant $(shell soroban config identity address grogu) \
		--pumping_level 15
