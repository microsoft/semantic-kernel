# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from unittest.mock import Mock, patch

from pytest import raises

from semantic_kernel.ai.open_ai.services.azure_text_embedding import AzureTextEmbedding
from semantic_kernel.ai.open_ai.services.open_ai_text_embedding import (
    OpenAITextEmbedding,
)

MODULE_PREFIX = "semantic_kernel.utils.auth_providers"


def test_azure_text_embedding_init() -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    # Test successful initialization
    azure_text_embedding = AzureTextEmbedding(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
        logger=logger,
    )

    assert azure_text_embedding._endpoint == endpoint
    assert azure_text_embedding._api_version == api_version
    assert azure_text_embedding._api_type == "azure"
    assert isinstance(azure_text_embedding, OpenAITextEmbedding)


def test_azure_text_embedding_init_with_empty_deployment_name() -> None:
    # deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    with raises(ValueError, match="The deployment name cannot be `None` or empty"):
        AzureTextEmbedding(
            deployment_name="",
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            logger=logger,
        )


def test_azure_text_embedding_init_with_empty_api_key() -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    # api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    with raises(ValueError, match="The Azure API key cannot be `None` or empty`"):
        AzureTextEmbedding(
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key="",
            api_version=api_version,
            logger=logger,
        )


def test_azure_text_embedding_init_with_empty_endpoint() -> None:
    deployment_name = "test_deployment"
    # endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    with raises(ValueError, match="The Azure endpoint cannot be `None` or empty"):
        AzureTextEmbedding(
            deployment_name=deployment_name,
            endpoint="",
            api_key=api_key,
            api_version=api_version,
            logger=logger,
        )


def test_azure_text_embedding_init_with_invalid_endpoint() -> None:
    deployment_name = "test_deployment"
    # endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    with raises(ValueError, match="The Azure endpoint must start with https://"):
        AzureTextEmbedding(
            deployment_name=deployment_name,
            endpoint="http://test-endpoint.com",
            api_key=api_key,
            api_version=api_version,
            logger=logger,
        )


def test_azure_chat_completion_init_with_auth_provider() -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    with patch(
        f"{MODULE_PREFIX}.__sk_auth_providers",
        {"test": lambda: (endpoint, api_key, True)},
    ):
        azure_chat_completion = AzureTextEmbedding(
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
        assert isinstance(azure_chat_completion, OpenAITextEmbedding)


def test_azure_chat_completion_init_with_missing_auth_provider() -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    with patch(
        f"{MODULE_PREFIX}.__sk_auth_providers",
        {
            "test": lambda: (endpoint, api_key, True),
            "test2": lambda: (endpoint, api_key, False),
        },
    ):
        with raises(
            ValueError,
            match=(
                "Failed to get auth from provider wrong: "
                "Auth provider 'wrong' not found. Registered providers: test, test2"
            ),
        ):
            AzureTextEmbedding(
                deployment_name=deployment_name,
                endpoint=None,
                api_key=None,
                api_version=api_version,
                logger=logger,
                auth_provider="wrong",
            )


def test_azure_text_embedding_setup_open_ai() -> None:
    import sys

    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    azure_text_embedding = AzureTextEmbedding(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
        logger=logger,
    )

    mock_openai = Mock()
    sys.modules["openai"] = mock_openai

    azure_text_embedding._setup_open_ai()

    assert mock_openai.api_type == "azure"
    assert mock_openai.api_key == api_key
    assert mock_openai.api_base == endpoint
    assert mock_openai.api_version == api_version
