SHELL = /bin/bash

.PHONY: help install install-uv install-python install-pre-commit install-sk clean build
.SILENT:  # not strictly required, but included per the original example
all: install

ifeq ($(PYTHON_VERSION),)
    PYTHON_VERSION = 3.10
endif

# Detect uv on PATH
UV_VERSION := $(shell command -v uv 2> /dev/null)

##############################
#  HELP
##############################
.ONESHELL:
help:
	echo -e "\033[1mUSAGE:\033[0m"
	echo "  make [target]"
	echo ""
	echo -e "\033[1mTARGETS:\033[0m"
	echo "  help                 - show this help message"
	echo "  install              - install uv, python, Semantic Kernel, and all dependencies"
	echo "                        This is the default and will use Python 3.10."
	echo "  install-uv           - install uv"
	echo "  install-python       - install multiple python distributions"
	echo "  install-sk           - install Semantic Kernel and all dependencies"
	echo "  install-pre-commit   - install pre-commit hooks"
	echo "  clean                - remove the virtualenvs"
	echo "  build                - build the project"
	echo ""
	echo -e "\033[1mVARIABLES:\033[0m"
	echo "  PYTHON_VERSION       - Python version to use. Default is 3.10"
	echo "                        By default, 3.10, 3.11, 3.12 and 3.13 are installed as well."

##############################
#  INSTALL
##############################
install:
	make install-uv
	make install-python
	make install-sk
	make install-pre-commit

##############################
#  INSTALL-UV
##############################
install-uv:
	# If uv is not found AND we haven't already re-invoked with CONTINUE=1...
ifneq ($(UV_VERSION),)
	echo "uv found at: $(UV_VERSION)"
	echo "running uv self update"
	uv self update
else ifeq ($(CONTINUE),1)
	echo "Skipping uv re-install; continuing with the rest of the steps."
else
	echo "uv could not be found."
	echo "Installing uv..."
	if [ -n "$$VIRTUAL_ENV" ]; then \
	    echo "Detected virtual environment at $$VIRTUAL_ENV, installing uv there..."; \
	    curl -LsSf https://astral.sh/uv/install.sh | INSTALL_DIR="$$VIRTUAL_ENV/bin" sh; \
	else \
	    echo "No virtual environment detected, installing uv globally..."; \
	    curl -LsSf https://astral.sh/uv/install.sh | sh; \
	fi
	echo "uv installed."
	echo "Re-executing shell so uv is immediately available on PATH..."
	exec $$SHELL -c 'make install CONTINUE=1'
endif

##############################
#  INSTALL-PYTHON
##############################
.ONESHELL:
install-python:
	echo "Installing python versions"
	uv python install 3.10 3.11 3.12 3.13

##############################
#  INSTALL-PRE-COMMIT
##############################
.ONESHELL:
install-pre-commit:
	echo "Installing pre-commit hooks"
	uv run pre-commit install -c python/.pre-commit-config.yaml

##############################
#  INSTALL-SK
##############################
.ONESHELL:
install-sk:
	echo "Creating and activating venv for python $(PYTHON_VERSION)"
	uv venv --python $(PYTHON_VERSION)
	echo "Installing Semantic Kernel and all dependencies"
	uv sync --all-extras --dev --prerelease=if-necessary-or-explicit

##############################
#  CLEAN
##############################
.ONESHELL:
clean:
	rm -rf .venv

##############################
#  BUILD
##############################
build:
	uvx --from build pyproject-build --installer uv
