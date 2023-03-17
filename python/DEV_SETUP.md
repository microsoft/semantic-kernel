# System setup

To get started, you'll need VSCode and a local installation of Python 3.x.

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

# LLM setup

Make sure you have an
[Open AI API Key](https://openai.com/api/) or
[Azure Open AI service key](https://learn.microsoft.com/azure/cognitive-services/openai/quickstart?pivots=rest-api)

ℹ️ **Note**: Azure OpenAI support is work in progress, and will be available soon.

Copy those keys into a `.env` file like this:

```
OPENAI_API_KEY=""
OPENAI_ORG_ID=""
AZURE_OPENAI_API_KEY=""
AZURE_OPENAI_ENDPOINT=""
```

We suggest adding a copy of the `.env` file under these folders:

- [python/tests](tests)
- [samples/notebooks/python](../samples/notebooks/python).

# Quickstart with Poetry

Poetry allows to use SK from the current repo, without worrying about paths, as
if you had SK pip package installed. SK pip package will be published after
porting all the major features and ensuring cross-compatibility with C# SDK.

To install Poetry in your system:

    pip3 install poetry

The following command install the project dependencies:

    poetry install

And the following activates the project virtual environment, to make it easier
running samples in the repo and developing apps using Python SK.

    poetry shell

To run the same checks that are run during the Azure Pipelines build, you can run:

    poetry run pre-commit run -c .conf/.pre-commit-config.yaml -a

# VSCode Setup

Open any of the `.py` files in the project and run the `Python: Select Interpreter` command
from the command palette. Make sure the virtual env (venv) created by `poetry` is selected.
The python you're looking for should be under `~/.cache/pypoetry/virtualenvs/semantic-kernel-.../bin/python`.

If prompted, install `black` and `flake8` (if VSCode doesn't find those packages,
it will prompt you to install them).

# Tests

You should be able to run the example under the [tests](tests) folder.
