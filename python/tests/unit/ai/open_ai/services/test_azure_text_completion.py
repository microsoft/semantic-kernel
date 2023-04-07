# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from unittest.mock import Mock

from pytest import raises

from semantic_kernel.ai.open_ai.services.azure_text_completion import (
    AzureTextCompletion,
)
from semantic_kernel.ai.open_ai.services.open_ai_text_completion import (
    OpenAITextCompletion,
)


def test_azure_text_completion_init() -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    # Test successful initialization
    azure_text_completion = AzureTextCompletion(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
        logger=logger,
    )

    assert azure_text_completion._endpoint == endpoint
    assert azure_text_completion._api_version == api_version
    assert azure_text_completion._api_type == "azure"
    assert isinstance(azure_text_completion, OpenAITextCompletion)


def test_azure_text_completion_init_with_empty_deployment_name() -> None:
    # deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    with raises(ValueError, match="The deployment name cannot be `None` or empty"):
        AzureTextCompletion(
            deployment_name="",
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            logger=logger,
        )


def test_azure_text_completion_init_with_empty_api_key() -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    # api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    with raises(ValueError, match="The Azure API key cannot be `None` or empty`"):
        AzureTextCompletion(
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key="",
            api_version=api_version,
            logger=logger,
        )


def test_azure_text_completion_init_with_empty_endpoint() -> None:
    deployment_name = "test_deployment"
    # endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    with raises(ValueError, match="The Azure endpoint cannot be `None` or empty"):
        AzureTextCompletion(
            deployment_name=deployment_name,
            endpoint="",
            api_key=api_key,
            api_version=api_version,
            logger=logger,
        )


def test_azure_text_completion_init_with_invalid_endpoint() -> None:
    deployment_name = "test_deployment"
    endpoint = "http://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    with raises(ValueError, match="The Azure endpoint must start with https://"):
        AzureTextCompletion(
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            logger=logger,
        )


def test_azure_text_completion_setup_open_ai() -> None:
    import sys

    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    azure_text_completion = AzureTextCompletion(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
        logger=logger,
    )

    mock_openai = Mock()
    sys.modules["openai"] = mock_openai

    azure_text_completion._setup_open_ai()

    assert mock_openai.api_type == "azure"
    assert mock_openai.api_key == api_key
    assert mock_openai.api_base == endpoint
    assert mock_openai.api_version == api_version
