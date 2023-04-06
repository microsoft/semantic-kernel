# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from sys import modules
from typing import Any
from unittest.mock import Mock

from pytest import fixture, raises

from semantic_kernel.ai.open_ai.services.azure_chat_completion import (
    AzureChatCompletion,
)
from semantic_kernel.ai.open_ai.services.open_ai_chat_completion import (
    OpenAIChatCompletion,
)


@fixture
def module() -> Any:
    import importlib

    spec = importlib.machinery.ModuleSpec("__sk_auth_providers", None)
    module = importlib.util.module_from_spec(spec)
    return module


def test_azure_chat_completion_init() -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    # Test successful initialization
    azure_chat_completion = AzureChatCompletion(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
        logger=logger,
    )

    assert azure_chat_completion._endpoint == endpoint
    assert azure_chat_completion._api_version == api_version
    assert azure_chat_completion._api_type == "azure"
    assert isinstance(azure_chat_completion, OpenAIChatCompletion)


def test_azure_chat_completion_init_with_empty_deployment_name() -> None:
    # deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    with raises(ValueError, match="The deployment name cannot be `None` or empty"):
        AzureChatCompletion(
            deployment_name="",
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            logger=logger,
        )


def test_azure_chat_completion_init_with_empty_api_key() -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    # api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    with raises(ValueError, match="The Azure API key cannot be `None` or empty`"):
        AzureChatCompletion(
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key="",
            api_version=api_version,
            logger=logger,
        )


def test_azure_chat_completion_init_with_empty_endpoint() -> None:
    deployment_name = "test_deployment"
    # endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    with raises(ValueError, match="The Azure endpoint cannot be `None` or empty"):
        AzureChatCompletion(
            deployment_name=deployment_name,
            endpoint="",
            api_key=api_key,
            api_version=api_version,
            logger=logger,
        )


def test_azure_chat_completion_init_with_invalid_endpoint() -> None:
    deployment_name = "test_deployment"
    # endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    with raises(ValueError, match="The Azure endpoint must start with https://"):
        AzureChatCompletion(
            deployment_name=deployment_name,
            endpoint="http://test-endpoint.com",
            api_key=api_key,
            api_version=api_version,
            logger=logger,
        )


def test_azure_chat_completion_init_with_auth_provider(module) -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    setattr(
        module,
        "providers",
        {
            "test": lambda: (endpoint, api_key, True),
        },
    )
    modules["__sk_auth_providers"] = module

    azure_chat_completion = AzureChatCompletion(
        deployment_name=deployment_name,
        endpoint=None,
        api_key=None,
        api_version=api_version,
        logger=logger,
        auth_provider="test",
    )

    assert azure_chat_completion._endpoint == endpoint
    assert azure_chat_completion._api_version == api_version
    assert azure_chat_completion._api_type == "azure_ad"
    assert isinstance(azure_chat_completion, OpenAIChatCompletion)


def test_azure_chat_completion_init_with_missing_auth_provider(module) -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    setattr(
        module,
        "providers",
        {
            "test": lambda: (endpoint, api_key, True),
            "test2": lambda: (endpoint, api_key, False),
        },
    )
    modules["__sk_auth_providers"] = module

    with raises(
        ValueError,
        match=(
            "Failed to get auth from provider wrong: "
            "Failed to load auth provider 'wrong'. Registered providers: test, test2"
        ),
    ):
        AzureChatCompletion(
            deployment_name=deployment_name,
            endpoint=None,
            api_key=None,
            api_version=api_version,
            logger=logger,
            auth_provider="wrong",
        )


def test_azure_chat_completion_setup_open_ai() -> None:
    import sys

    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    azure_chat_completion = AzureChatCompletion(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
        logger=logger,
    )

    mock_openai = Mock()
    sys.modules["openai"] = mock_openai

    azure_chat_completion._setup_open_ai()

    assert mock_openai.api_type == "azure"
    assert mock_openai.api_key == api_key
    assert mock_openai.api_base == endpoint
    assert mock_openai.api_version == api_version
