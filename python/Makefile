SHELL = bash

.PHONY: help install recreate-env pre-commit

help:
	@echo -e "\033[1mUSAGE:\033[0m"
	@echo "  make [target]"
	@echo ""
	@echo -e "\033[1mTARGETS:\033[0m"
	@echo "  install              - install Poetry and project dependencies"
	@echo "  install-pre-commit   - install and configure pre-commit hooks"
	@echo "  pre-commit           - run pre-commit hooks on all files"
	@echo "  recreate-env         - destroy and recreate Poetry's virtualenv"

.ONESHELL:
install:
	@# Check to make sure Python is installed
	@if ! command -v python3 &> /dev/null
	then
		echo "Python could not be found"
		echo "Please install Python"
		exit 1
	fi

	@# Check if Poetry is installed
	@if ! command -v poetry &> /dev/null
	then
		echo "Poetry could not be found"
		echo "Installing Poetry"
		curl -sSL https://install.python-poetry.org | python3 -
	fi 

	# Install the dependencies
	poetry install

.ONESHELL:
recreate-env:
	# Stop the current virtualenv if active or alternative use
	# `exit` to exit from a Poetry shell session
	(deactivate || exit 0)

	# Remove all the files of the current environment of the folder we are in
	export POETRY_LOCATION=$$(poetry env info -p) 
	echo "Poetry is $${POETRY_LOCATION}"
	rm -rf "$${POETRY_LOCATION}"

pre-commit:
	poetry run pre-commit run --all-files -c .conf/.pre-commit-config.yaml

.ONESHELL:
install-pre-commit:
	poetry run pre-commit install
	# Edit the pre-commit config file to change the config path
	sed -i 's|\.pre-commit-config\.yaml|\.conf/\.pre-commit-config\.yaml|g' .git/hooks/pre-commit
