.PHONY: help install run
.DEFAULT_GOAL := help
SHELL:=/bin/bash

ifndef CONTRACT_HASH_PUMPIT
   override CONTRACT_HASH_PUMPIT = "CAR7DAS2IGV2E542R4EJRDV7QQERQFLQZRZWVQEE7J3G4R65RLWSO53B"
endif

ifndef CLAIMANT_ADDR_SECRET_PUMPIT
   override CLAIMANT_ADDR_SECRET_PUMPIT = ...
endif

# Add help text after each target name starting with '\#\#'
help:   ## show this help
	@echo -e "Help for this makefile\n"
	@echo "Possible commands are:"
	@grep -h "##" $(MAKEFILE_LIST) | grep -v grep | sed -e 's/\(.*\):.*##\(.*\)/    \1: \2/'

install:  ## install Python dependencies
	# Python part
	python -m venv venv
	source venv/bin/activate
	pip install .

run:
	source venv/bin/activate
	CONTRACT_HASH_PUMPIT=$(CONTRACT_HASH_PUMPIT) CLAIMANT_ADDR_SECRET_PUMPIT=$(CLAIMANT_ADDR_SECRET_PUMPIT) python pumpit.py
