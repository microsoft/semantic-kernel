This document describes how to setup your environment with Python and Poetry,
if you're working on new features or a bug fix for Semantic Kernel, or simply
want to run the tests included.

# LLM setup

Make sure you have an
[Open AI API Key](https://openai.com/api/) or
[Azure Open AI service key](https://learn.microsoft.com/azure/cognitive-services/openai/quickstart?pivots=rest-api)

Copy those keys into a `.env` file (see the `.env.example` file):

```
OPENAI_API_KEY=""
OPENAI_ORG_ID=""
AZURE_OPENAI_DEPLOYMENT_NAME=""
AZURE_OPENAI_ENDPOINT=""
AZURE_OPENAI_API_KEY=""
```

We suggest adding a copy of the `.env` file under these folders:

- [python/tests](tests)
- [samples/notebooks/python](../samples/notebooks/python).

# System setup

To get started, you'll need VSCode and a local installation of Python 3.8+.

You can run:

    python3 --version ; pip3 --version ; code -v

to verify that you have the required dependencies.

## If you're on WSL

Check that you've cloned the repository to `~/workspace` or a similar folder.
Avoid `/mnt/c/` and prefer using your WSL user's home directory.

Ensure you have the WSL extension for VSCode installed (and the Python extension
for VSCode installed).

You'll also need `pip3` installed. If you don't yet have a `python3` install in WSL,
you can run:

```bash
sudo apt-get update && sudo apt-get install python3 python3-pip
```

ℹ️ **Note**: if you don't have your PATH setup to find executables installed by `pip3`,
you may need to run `~/.local/bin/poetry install` and `~/.local/bin/poetry shell`
instead. You can fix this by adding `export PATH="$HOME/.local/bin:$PATH"` to
your `~/.bashrc` and closing/re-opening the terminal.\_

# Using Poetry

Poetry allows to use SK from the local files, without worrying about paths, as
if you had SK pip package installed.

To install Poetry in your system, first, navigate to the directory containing
this README using your chosen shell. You will need to have Python 3.8+ installed.

Install the Poetry package manager and create a project virtual environment.
Note: SK requires at least Poetry 1.2.0.

```bash
# Install poetry package
pip3 install poetry

# Use poetry to install base project dependencies
poetry install

# If you want to use connectors such as hugging face
# poetry install --with <connector group name>
# example: poetry install --with hugging_face

# Use poetry to activate project venv
poetry shell
```

# VSCode Setup

Open any of the `.py` files in the project and run the `Python: Select Interpreter`
command from the command palette. Make sure the virtual env (venv) created by
`poetry` is selected.
The python you're looking for should be under `~/.cache/pypoetry/virtualenvs/semantic-kernel-.../bin/python`.

If prompted, install `black` and `flake8` (if VSCode doesn't find those packages,
it will prompt you to install them).

# Tests

You can run the unit tests under the [tests/unit](tests/unit/) folder.

    cd python
    poetry install
    poetry run pytest tests/unit

You can run the integration tests under the [tests/integration](tests/integration/) folder.

    cd python
    poetry install
    poetry run pytest tests/integration

You can also run all the tests together under the [tests](tests/) folder.

    cd python
    poetry install
    poetry run pytest tests

# Tools and scripts

## Pipeline checks

To run the same checks that run during the GitHub Action build, you can use
this command, from the [python](../python) folder:

    poetry run pre-commit run -c .conf/.pre-commit-config.yaml -a

## Running ruff

    poetry run ruff check .
