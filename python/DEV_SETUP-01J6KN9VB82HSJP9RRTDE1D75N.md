---
runme:
  document:
    relativePath: DEV_SETUP.md
  session:
    id: 01J6KN9VB82HSJP9RRTDE1D75N
    updated: 2024-08-31 07:34:40Z
---

# Dev Setup

This document describes how to setup your environment with Python and Poetry,
if you're working on new features or a bug fix for Semantic Kernel, or simply
want to run the tests included.

## LLM setup

Make sure you have an
[OpenAI API Key](ht***********************om) or
[Azure OpenAI service key](ht**********************************************************************************pi)

There are two methods to manage keys, secrets, and endpoints:

1. Store them in environment variables. SK Python leverages pydantic settings to load keys, secrets, and endpoints. This means that there is a first attempt to load them from environment variables. The `.env` file naming applies to how the names should be stored as environment variables.
2. If you'd like to use the `.env` file, you will need to configure the `.env` file with the following keys into a `.env` file (see the `.env.example` file):

```sh {"id":"01J6KNPX0HTGAZ4YDQ34296TT7"}
OPENAI_API_KEY=""
OPENAI_ORG_ID=""
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=""
AZURE_OPENAI_TEXT_DEPLOYMENT_NAME=""
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=""
AZURE_OPENAI_ENDPOINT=""
AZURE_OPENAI_API_KEY=""
```

You will then configure the Text/ChatCompletion class with the keyword argument `env_file_path`:

```python {"id":"01J6KNPX0HTGAZ4YDQ353PQS4G"}
chat_completion = OpenAIChatCompletion(service_id="test", env_file_path=<path_to_file>)
```

This optional `env_file_path` parameter will allow pydantic settings to use the `.env` file as a fallback to read the settings.

If using the second method, we suggest adding a copy of the `.env` file under these folders:

- [./tests](./tests)
- [./samples/getting_started](./samples/getting_started).

## System setup

To get started, you'll need VSCode and a local installation of Python 3.8+.

You can run:

```python {"id":"01J6KNPX0HTGAZ4YDQ3625T9E4"}
    py***n3 --version ; pip3 --version ; code -v
```

to verify that you have the required dependencies.

## If you're on WSL

Check that you've cloned the repository to `~/workspace` or a similar folder.
Avoid `/mnt/c/` and prefer using your WSL user's home directory.

Ensure you have the WSL extension for VSCode installed (and the Python extension
for VSCode installed).

You'll also need `pip3` installed. If you don't yet have a `py***n3` install in WSL,
you can run:

```bash {"id":"01J6KNPX0HTGAZ4YDQ366SG3QM"}
sudo apt-get update && sudo apt-get install py***n3 py*******ip
```

ℹ️ __Note__: if you don't have your PATH setup to find executables installed by `pip3`,
you may need to run `~/.local/bin/poetry install` and `~/.local/bin/poetry shell`
instead. You can fix this by adding `export PATH="$HOME/.local/bin:$PATH"` to
your `~/.bashrc` and closing/re-opening the terminal.\_

## Using Poetry

Poetry allows to use SK from the local files, without worrying about paths, as
if you had SK pip package installed.

To install Poetry in your system, first, navigate to the directory containing
this README using your chosen shell. You will need to have Python 3.10, 3.11, or 3.12
installed.

Install the Poetry package manager and create a project virtual environment.
Note: SK requires at least Poetry 1.2.0.

### Note for MacOS Users

It is best to install Poetry using their
[official installer](ht******************************************************************er).

On MacOS, you might find that `python` commands are not recognized by default,
and you can only use `py***n3`. To make it easier to run `python ...` commands
(which Poetry requires), you can create an alias in your shell configuration file.

Follow these steps:

1. **Open your shell configuration file**:

   - For __Bash__: `nano ~/.bash_profile` or `nano ~/.bashrc`
   - For **Zsh** (default on macOS Catalina and later): `nano ~/.zshrc`

2. **Add the alias**:

```sh {"id":"01J6KNPX0HTGAZ4YDQ37NQ12T9"}
alias py**on='py***n3'
```

3. **Save the file and exit**:

   - In `nano`, press `CTRL + X`, then `Y`, and hit `Enter`.

4. **Apply the changes**:

   - For __Bash__: `source ~/.bash_profile` or `source ~/.bashrc`
   - For **Zsh**: `source ~/.zshrc`

After these steps, you should be able to use `python` in your terminal to run
Python 3 commands.

### Poetry Installation

```bash {"id":"01J6KNPX0HTGAZ4YDQ3BB96MAY"}
# Install poetry package if not choosing to install via their official installer
pip3 install poetry

# optionally, define which python version you want to use
poetry env use py******11

# Use poetry to install base project dependencies
poetry install

# If you want to get all dependencies for tests installed, use
# poetry install --with tests
# example: poetry install --with hugging_face

# Use poetry to activate project venv
poetry shell

# Optionally, you can install the pre-commit hooks
poetry run pre-commit install
# this will run linters and mypy checks on all the changed code.
```

## VSCode Setup

Open the [workspace](ht************************************************es) in VSCode.

> The Python workspace is the `./python` folder if you are at the root of the repository.

Open any of the `.py` files in the project and run the `Python: Select Interpreter`
command from the command palette. Make sure the virtual env (venv) created by
`poetry` is selected.
The python you're looking for should be under `~/.cache/pypoetry/virtualenvs/semantic-kernel-.../bin/python`.

If prompted, install `ruff`. (It should have been installed as part of `poetry install`).

You also need to install the `ruff` extension in VSCode so that auto-formatting uses the `ruff` formatter on save.
Read more about the extension here: ht************************************de

## Tests

You can run the unit tests under the [tests/unit](tests/unit/) folder.

```bash {"id":"01J6KNPX0HTGAZ4YDQ3CVYSJC6"}
    poetry install --with unit-tests
    poetry run pytest tests/unit
```

Alternatively, you can run them using VSCode Tasks. Open the command palette
(`Ctrl+Shift+P`) and type `Tasks: Run Task`. Select `Python: Tests - Unit` or `Python: Tests - Code Coverage` from the list.

You can run the integration tests under the [tests/integration](tests/integration/) folder.

```bash {"id":"01J6KNPX0HTGAZ4YDQ3ETP16N9"}
    poetry install --with tests
    poetry run pytest tests/integration
```

You can also run all the tests together under the [tests](tests/) folder.

```bash {"id":"01J6KNPX0HTGAZ4YDQ3GYN6VJR"}
    poetry install
    poetry run pytest tests
```

Alternatively, you can run them using VSCode Tasks. Open the command palette
(`Ctrl+Shift+P`) and type `Tasks: Run Task`. Select `Python: Tests - All` from the list.

## Tools and scripts

## Implementation Decisions

### Asynchronous programming

It's important to note that most of this library is written with asynchronous in mind. The
developer should always assume everything is asynchronous. One can use the function signature
with either `async def` or `def` to understand if something is asynchronous or not.

### Documentation

Each file should have a single first line containing: # Copyright (c) Microsoft. All rights reserved.

We follow the [Google Docstring](ht***********************************************************************************ds) style guide for functions and methods.
They are currently not checked for private functions (functions starting with '_').

They should contain:

- Single line explaining what the function does, ending with a period.
- If necessary to further explain the logic a newline follows the first line and then the explanation is given.
- The following three sections are optional, and if used should be separated by a single empty line.
- Arguments are then specified after a header called `Args:`, with each argument being specified in the following format:
   - `arg_name` (`arg_type`): Explanation of the argument, arg_type is optional, as long as you are consistent.
   - if a longer explanation is needed for a argument, it should be placed on the next line, indented by 4 spaces.
   - Default values do not have to be specified, they will be pulled from the definition.

- Returns are specified after a header called `Returns:` or `Yields:`, with the return type and explanation of the return value.
- Finally, a header for exceptions can be added, called `Raises:`, with each exception being specified in the following format:
   - `ExceptionType`: Explanation of the exception.
   - if a longer explanation is needed for a exception, it should be placed on the next line, indented by 4 spaces.

Putting them all together, gives you at minimum this:

```python {"id":"01J6KNPX0HTGAZ4YDQ3GZ160F4"}
def eq******g1: str, arg2: str) -> bool:
    """Compares two strings and returns True if they are the same."""
    ...
```

Or a complete version of this:

```python {"id":"01J6KNPX0HTGAZ4YDQ3JGT3D67"}
def eq******g1: str, arg2: str) -> bool:
    """Compares two strings and returns True if they are the same.

    Here is extra explanation of the logic involved.

    Args:
        arg1 (str): The first string to compare.
        arg2 (str): The second string to compare.
            This string requires extra explanation.

    Returns:
        bool: True if the strings are the same, False otherwise.

    Raises:
        ValueError: If one of the strings is empty.
    """
    ...
```

If in doubt, use the link above to read much more considerations of what to do and when, or use common sense.

## Pydantic and Serialization

[Pydantic Do*********on](ht**************************10/)

### Overview

This section describes how one can enable serialization for their class using Pydantic.

### Upgrading existing classes to use Pydantic

Let's take the following example:

```python {"id":"01J6KNPX0HTGAZ4YDQ3JKQTX8W"}
class A:
    def __init__(self, a: int, b: float, c: List[float], d: dict[str, tuple[float, str]] = {}):
        self.a = a
        self.b = b
        self.c = c
        self.d = d
```

You would convert this to a Pydantic class by subclassing from the `KernelBaseModel` class.

```python {"id":"01J6KNPX0HTGAZ4YDQ3JZ43C10"}
from pydantic import Field
from semantic_kernel.kernel_pydantic import KernelBaseModel

class A(KernelBaseModel):
    # The notation for the fields is similar to dataclasses.
    a: int
    b: float
    c: list[float]
    # Only, instead of using dataclasses.field, you would use pydantic.Field
    d: dict[str, tuple[float, str]] = Field(default_factory=dict)
```

 Classes with data that need to be serialized, and some of them are Generic types

Let's take the following example:

```python {"id":"01J6KNPX0HTGAZ4YDQ3PC4NBD0"}
from typing import TypeVar

T1 = Ty***ar("T1")
T2 = Ty***ar("T2", bound=<some class>)

class A:
    def __init__(a: int, b: T1, c: T2):
        self.a = a
        self.b = b
        self.c = c
```

You can use the `KernelBaseModel` to convert these to pydantic serializable classes.

```python {"id":"01J6KNPX0HTGAZ4YDQ3R7VE7KV"}
from typing import Generic

from semantic_kernel.kernel_pydantic import KernelBaseModel

class A(KernelBaseModel, Ge***ic[T1, T2]):
    # T1 and T2 must be specified in the Generic argument otherwise, pydantic will
    # NOT be able to serialize this class
    a: int
    b: T1
    c: T2
```

## Pipeline checks

To run the same checks that run during the GitHub Action build, you can use
this command, from the [python](../python) folder:

```bash {"id":"01J6KNPX0HTGAZ4YDQ3RB8FHQJ"}
    poetry run pre-commit run -a
```

or use the following task (using `Ctrl+Shift+P`):

- `Python - Run Checks` to run the checks on the whole project.
- `Python - Run Checks - Staged` to run the checks on the currently staged files only.

Ideally you should run these checks before committing any changes, use `poetry run pre-commit install` to set that up.

## Code Coverage

We try to maintain a high code coverage for the project. To run the code coverage on the unit tests, you can use the following command:

```bash {"id":"01J6KNPX0HTGAZ4YDQ3V7S5W7V"}
    poetry run pytest --cov=semantic_kernel --cov-report=term-missing:skip-covered tests/unit/
```

or use the following task (using `Ctrl+Shift+P`):

- `Python: Tests - Code Coverage` to run the code coverage on the whole project.

This will show you which files are not covered by the tests, including the specific lines not covered.

## Catching up with the latest changes

There are many people committing to Semantic Kernel, so it is important to keep your local repository up to date. To do this, you can run the following commands:

```bash {"id":"01J6KNPX0J3RHKXXPZZ2645V13"}
    git fetch upstream main
    git rebase upstream/main
    git push --force-with-lease
```

or:

```bash {"id":"01J6KNPX0J3RHKXXPZZ3T5EN1R"}
    git fetch upstream main
    git merge upstream/main
    git push
```

This is assuming the upstream branch refers to the main repository. If you have a different name for the upstream branch, you can replace `upstream` with the name of your upstream branch.

After running the rebase command, you may need to resolve any conflicts that arise. If you are unsure how to resolve a conflict, please refer to the [GitHub's documentation on resolving conflicts](ht*****************************************************************************************se), or for [VSCode](ht**********************************************************************ts).
