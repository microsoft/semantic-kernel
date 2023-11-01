# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from unittest.mock import AsyncMock, call, patch

import pytest

from semantic_kernel.connectors.ai.open_ai.services.azure_text_embedding import (
    AzureTextEmbedding,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_embedding import (
    OpenAITextEmbedding,
)


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

    with pytest.raises(
        ValueError, match="The deployment name cannot be `None` or empty"
    ):
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

    with pytest.raises(
        ValueError, match="The Azure API key cannot be `None` or empty`"
    ):
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

    with pytest.raises(
        ValueError, match="The Azure endpoint cannot be `None` or empty"
    ):
        AzureTextEmbedding(
            deployment_name=deployment_name,
            endpoint="",
            api_key=api_key,
            api_version=api_version,
            logger=logger,
        )


def test_azure_text_embedding_init_with_invalid_endpoint() -> None:
    deployment_name = "test_deployment"
    endpoint = "http://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    with pytest.raises(ValueError, match="The Azure endpoint must start with https://"):
        AzureTextEmbedding(
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            logger=logger,
        )


@pytest.mark.asyncio
async def test_azure_text_embedding_calls_with_parameters() -> None:
    mock_openai = AsyncMock()
    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_text_embedding.openai",
        new=mock_openai,
    ):
        deployment_name = "test_deployment"
        endpoint = "https://test-endpoint.com"
        api_key = "test_api_key"
        api_type = "azure"
        api_version = "2023-03-15-preview"
        logger = Logger("test_logger")
        texts = ["hello world", "goodbye world"]

        azure_text_embedding = AzureTextEmbedding(
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            logger=logger,
        )

        await azure_text_embedding.generate_embeddings_async(texts)

        mock_openai.Embedding.acreate.assert_called_once_with(
            engine=deployment_name,
            api_key=api_key,
            api_type=api_type,
            api_base=endpoint,
            api_version=api_version,
            organization=None,
            input=texts,
        )


@pytest.mark.asyncio
async def test_azure_text_embedding_calls_with_batches() -> None:
    mock_openai = AsyncMock()
    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_text_embedding.openai",
        new=mock_openai,
    ):
        deployment_name = "test_deployment"
        endpoint = "https://test-endpoint.com"
        api_key = "test_api_key"
        api_type = "azure"
        api_version = "2023-03-15-preview"
        logger = Logger("test_logger")
        texts = [i for i in range(0, 5)]

        azure_text_embedding = AzureTextEmbedding(
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            logger=logger,
        )

        await azure_text_embedding.generate_embeddings_async(texts, batch_size=3)

        mock_openai.assert_has_calls(
            [
                call.Embedding.acreate(
                    engine=deployment_name,
                    api_key=api_key,
                    api_type=api_type,
                    api_base=endpoint,
                    api_version=api_version,
                    organization=None,
                    input=texts[0:3],
                ),
                call.Embedding.acreate().__getitem__("data"),
                call.Embedding.acreate().__getitem__().__iter__(),
                call.Embedding.acreate(
                    engine=deployment_name,
                    api_key=api_key,
                    api_type=api_type,
                    api_base=endpoint,
                    api_version=api_version,
                    organization=None,
                    input=texts[3:5],
                ),
            ],
            any_order=False,
        )
