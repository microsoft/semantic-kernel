# Getting set up

To get started, you'll need VSCode and a local installation of Python 3.x. 

You can run: `python3 --version ; pip3 --version ; code -v` to verify that you have the required dependencies.

## If you're on WSL

Check that you've cloned the repository to `~/workspace` or a similar folder (avoid `/mnt/c/` and prefer using your WSL user's home directory).

Ensure you have the WSL extension for VSCode installed (and the Python extension for VSCode installed).

You'll also need `pip3` installed. If you don't yet have a `python3` install in WSL, you can run:
```bash
sudo apt-get update && sudo apt-get install python3 python3-pip
```

Now run the following commands:

```bash
# Install poetry package
pip3 install poetry
# Use poetry to install project deps
poetry install
# Use poetry to activate project venv
poetry shell
```

_Note: if you don't have your PATH setup to find executables installed by `pip3`, you may need to run `~/.local/bin/poetry install` and `~/.local/bin/poetry shell` instead. You can fix this by adding `export PATH="$HOME/.local/bin:$PATH"` to your `~/.bashrc` and closing/re-opening the terminal._

## If you're on `*nix`

Run the following commands:

```bash
# Install poetry package
pip3 install poetry
# Use poetry to install project deps
poetry install
# Use poetry to activate project venv
poetry shell
```

## VSCode Setup

Open any of the `.py` files in the project and run the `Python: Select Interpreter` command from the command palette. Make sure the virtual env (venv) created by `poetry` is selected. (The python you're looking for should be under `~/.cache/pypoetry/virtualenvs/semantic-kernel-.../bin/python`.)

If prompted, install `black` and `flake8` (if VSCode doesn't find those packages, it will prompt you to install them).

To run the same checks that are run during the Azure Pipelines build, you can run: `poetry run pre-commit run -c .conf/.pre-commit-config.yaml -a`.
