# Copyright (c) Microsoft. All rights reserved.

from __future__ import annotations

import os
import warnings
from typing import Optional

import pytest

from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.kernel import Kernel
from semantic_kernel.utils.settings import (
    azure_openai_settings_from_dot_env,
    google_palm_settings_from_dot_env,
    openai_settings_from_dot_env,
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


@pytest.fixture(scope="function")
def create_kernel(plugin: Optional[KernelPlugin] = None):
    kernel = Kernel()
    if plugin:
        kernel.add_plugin(plugin)
    return kernel


@pytest.fixture(scope="session")
def get_aoai_config():
    if "Python_Integration_Tests" in os.environ:
        deployment_name = os.environ["AzureOpenAIEmbeddings__DeploymentName"]
        api_key = os.environ["AzureOpenAI_EastUS__ApiKey"]
        endpoint = os.environ["AzureOpenAI_EastUS__Endpoint"]
    else:
        # Load credentials from .env file
        deployment_name, api_key, endpoint = azure_openai_settings_from_dot_env()
        deployment_name = "text-embedding-ada-002"

    return deployment_name, api_key, endpoint


@pytest.fixture(scope="session")
def get_oai_config():
    if "Python_Integration_Tests" in os.environ:
        api_key = os.environ["OpenAI__ApiKey"]
        org_id = None
    else:
        # Load credentials from .env file
        api_key, org_id = openai_settings_from_dot_env()

    return api_key, org_id


@pytest.fixture(scope="session")
def get_gp_config():
    if "Python_Integration_Tests" in os.environ:
        api_key = os.environ["GOOGLE_PALM_API_KEY"]
    else:
        # Load credentials from .env file
        api_key = google_palm_settings_from_dot_env()

    return api_key
