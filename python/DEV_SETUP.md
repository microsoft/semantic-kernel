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
- [./notebooks](./notebooks).

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

## Pydantic and Serialization

[Pydantic Documentation](https://docs.pydantic.dev/1.10/)

### Overview

This section describes how one can enable serialization for their class using Pydantic.

IMPORTANT: This document (and SemanticKernel) currently use Pydantic 1.x. When SK is upgraded
to use Pydantic 2.x, this document will be upgraded accordingly.

### Terminology

There are 3 types of classes you need to be aware of when enabling serialization with Pydantic:

1. Classes which contain no data - examples are Protocols, ABC subclasses and any other classes
   that don't contain any data that needs to be serialized.
2. Classes which contain data that need to be serialized, but don't contain any generic classes.
3. Classes which contain data that need to be serialized, AND contain generic classes.

### Upgrading existing classes to use Pydantic

#### Classes without any data

Let's take the following classes as examples - 1 ABC, 1 Protocol, and 1 class that only contains
data that doesn't need to be serialized.

```python
class A(Protocol):
    def some_method(self, *args, **kwargs): ...

class B(ABC):
    def some_method(self, *args, **kwargs): ...

class C:
    def __init__(self):
        # IMPORTANT: These variables are NOT being passed into the initializer
        # so they don't need to be serialized. If the are though, you'll have
        # to treat this as a class that contains data that needs to be serialized
        self._a = ...
```

For `Protocol` subclasses, nothing needs to be done, and they can be left as is.

For the remaining types, SemanticKernel provides a class named `PydanticField`. Subclassing
from this field is sufficient to have these types of classes as valid Pydantic fields, and allows
any class using them as attributes to be serialized.

```python
from semantic_kernel.sk_pydantic import PydanticField

class B(PydanticField): ... # correct, B is still an ABC because PydanticField subclasses ABC
class B(PydanticField, ABC): ... # Also correct
class B(ABC, PydanticField): ... # ERROR: Python cannot find a valid super class ordering.

class C(PydanticField): ... # No other changes needed
```

The classes B and C can now be used as valid Pydantic Field annotations.

````python
from pydantic import BaseModel

class MyModel(BaseModel):
    b: B
    c: C

Class A can only be used as a Pydantic Field annotation for a Pydantic BaseModel subclass
which is configured to allow arbitrary field types like so:

```python
from pydantic import BaseModel
class IncorrectModel(BaseModel):
    a: A  # Pydantic error

class CorrectModel(BaseModel):
    a: A  # Okay
    class Config:  # Configuration that tells Pydantic to allow field types that it can't serialize
        arbitrary_types_allowed = True
````

#### Classes with data, but no Generic types that need to be serialized

If your class has any data that needs to be serialized, but the field annotation for that data type
in your class is not a Generic type, this section applies to you.

Let's take the following example:

```python
class A:
    def __init__(self, a: int, b: float, c: List[float], d: dict[str, tuple[float, str]] = {}):
        # Since a, b, c and d are needed to initialize this class, they need to be serialized
        # if can be serialized.
        # Although a, b, c and d are builtin python types, any valid pydantic field can be used
        # here. This includes the classes defined in the previous category.
        self.a = a
        self.b = b
        self.c = c
        self.d = d
```

You would convert this to a Pydantic class by subclassing from the `SKBaseModel` class.

```python
from pydantic import Field
from semantic_kernel.sk_pydantic import SKBaseModel

class A(SKBaseModel):
    # The notation for the fields is similar to dataclasses.
    a: int
    b: float
    c: List[float]
    # Only, instead of using dataclasses.field, you would use pydantic.Field
    d: dict[str, tuple[flost, str]] = Field(default_factory=dict)
```

#### Classes with data that need to be serialized, and some of them are Generic types

Let's take the following example:

```python
from typing import TypeVar

T1 = TypeVar("T1")
T2 = TypeVar("T2", bound=<some class>)

class A:
    def __init__(a: int, b: T1, c: T2):
        self.a = a
        self.b = b
        self.c = c
```

You can uses the `SKGenericModel` to convert these to pydantic serializable classes.

```python
from typing import Generic

from semantic_kernel.sk_pydantic import SKGenericModel

class A(SKGenericModel, Generic[T1, T2]):
    # T1 and T2 must be specified in the Generic argument otherwise, pydantic will
    # NOT be able to serialize this class
    a: int
    b: T1
    c: T2
```

## Pipeline checks

To run the same checks that run during the GitHub Action build, you can use
this command, from the [python](../python) folder:

    poetry run pre-commit run -c .conf/.pre-commit-config.yaml -a
