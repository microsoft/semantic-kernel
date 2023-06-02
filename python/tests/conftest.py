# Copyright (c) Microsoft. All rights reserved.

import os

import pytest

import semantic_kernel as sk
from semantic_kernel.settings import KernelSettings, OpenAISettings, load_settings


@pytest.fixture()
def create_kernel():
    kernel = sk.Kernel()
    return kernel


@pytest.fixture()
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


@pytest.fixture()
def kernel_settings() -> KernelSettings:
    """Settings used for testing.

    NOTE: See the `tests/unit/test_settings.py::test_load_settings` test for a test that
    ensures that we can load the settings in the test environment. If that test fails,
    then any test depending on this fixture will also fail.
    """
    return load_settings()


@pytest.fixture()
def openai_settings(kernel_settings: KernelSettings) -> OpenAISettings:
    """OpenAI settings used for testing."""
    return kernel_settings.openai
