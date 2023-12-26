.PHONY: help install run
.DEFAULT_GOAL := help
SHELL:=/bin/bash

ifndef CONTRACT_HASH_PUMPIT
   override CONTRACT_HASH_PUMPIT = ...
endif

ifndef CLAIMANT_ADDR_PUMPIT
   override CLAIMANT_ADDR_PUMPIT = ...
endif

# Add help text after each target name starting with '\#\#'
help:   ## show this help
	@echo -e "Help for this makefile\n"
	@echo "Possible commands are:"
	@grep -h "##" $(MAKEFILE_LIST) | grep -v grep | sed -e 's/\(.*\):.*##\(.*\)/    \1: \2/'

install:  ## install Rust, Soroban-CLI and Python dependencies
	sudo apt-get install libopenblas-dev
	# install Rust
	curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
	# install Soroban and config
	rustup target add wasm32-unknown-unknown
	cargo install --locked soroban-cli --features opt
	# Python part
	python -m venv venv
	source venv/bin/activate
	pip install .

run:
	source venv/bin/activate
	python pumpit.py
