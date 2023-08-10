# Copyright (c) Microsoft. All rights reserved.

import os
import typing as t
import warnings

import pytest

import semantic_kernel as sk
from semantic_kernel.memory.null_memory import NullMemory
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.orchestration.sk_function import SKFunction
from semantic_kernel.skill_definition.read_only_skill_collection import (
    ReadOnlySkillCollection,
)


@pytest.fixture(autouse=True)
def enable_debug_mode():
    """Set `autouse=True` to enable easy debugging for tests.

    How to debug:
    1. Ensure [snoop](https://github.com/alexmojaki/snoop) is installed
        (`pip install snoop`).
    2. If you're doing print based debugging, use `pr` instead of `print`.
        That is, convert `print(some_var)` to `pr(some_var)`.
    3. If you want a trace of a particular functions calls, just add `ss()` as the first
        line of the function.

    NOTE:
    ----
        It's completely fine to leave `autouse=True` in the fixture. It doesn't affect
        the tests unless you use `pr` or `ss` in any test.

    NOTE:
    ----
        When you use `ss` or `pr` in a test, pylance or mypy will complain. This is
        because they don't know that we're adding these functions to the builtins. The
        tests will run fine though.
    """
    import builtins

    try:
        import snoop
    except ImportError:
        warnings.warn(
            "Install snoop to enable trace debugging. `pip install snoop`",
            ImportWarning,
        )
        return

    builtins.ss = snoop.snoop(depth=4).__enter__
    builtins.pr = snoop.pp


@pytest.fixture(scope="session")
def create_kernel():
    kernel = sk.Kernel()
    return kernel


@pytest.fixture(scope="session")
def get_aoai_config():
    if "Python_Integration_Tests" in os.environ:
        deployment_name = os.environ["AzureOpenAIEmbeddings__DeploymentName"]
        api_key = os.environ["AzureOpenAI__ApiKey"]
        endpoint = os.environ["AzureOpenAI__Endpoint"]
    else:
        # Load credentials from .env file
        deployment_name, api_key, endpoint = sk.azure_openai_settings_from_dot_env()
        deployment_name = "text-embedding-ada-002"

    return deployment_name, api_key, endpoint


@pytest.fixture(scope="session")
def get_oai_config():
    if "Python_Integration_Tests" in os.environ:
        api_key = os.environ["OpenAI__ApiKey"]
        org_id = None
    else:
        # Load credentials from .env file
        api_key, org_id = sk.openai_settings_from_dot_env()

    return api_key, org_id


@pytest.fixture()
def context_factory() -> t.Callable[[ContextVariables], SKContext]:
    """Return a factory for SKContext objects."""

    def create_context(
        context_variables: ContextVariables, *functions: SKFunction
    ) -> SKContext:
        """Return a SKContext object."""
        return SKContext(
            context_variables,
            NullMemory(),
            skill_collection=ReadOnlySkillCollection(
                data={
                    ReadOnlySkillCollection.GLOBAL_SKILL.lower(): {
                        f.name: f for f in functions
                    }
                },
            ),
        )

    return create_context
