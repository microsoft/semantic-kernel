# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from unittest.mock import AsyncMock, call, patch

import pytest
from pydantic import ValidationError

from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import (
    EmbeddingGeneratorBase,
)
from semantic_kernel.connectors.ai.open_ai.services.azure_text_embedding import (
    AzureTextEmbedding,
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

    assert azure_text_embedding.endpoint == endpoint
    assert azure_text_embedding.api_version == api_version
    assert azure_text_embedding.api_type == "azure"
    assert isinstance(azure_text_embedding, EmbeddingGeneratorBase)


def test_azure_text_embedding_init_with_empty_deployment_name() -> None:
    # deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")

    with pytest.raises(ValidationError, match="deployment_name"):
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

    with pytest.raises(ValidationError, match="api_key"):
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

    with pytest.raises(ValidationError, match="endpoint"):
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

    with pytest.raises(ValidationError, match="https"):
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
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_handler.openai",
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
            deployment_id=deployment_name,
            api_key=api_key,
            api_type=api_type,
            api_base=endpoint,
            api_version=api_version,
            input=texts,
        )


@pytest.mark.asyncio
async def test_azure_text_embedding_calls_with_batches() -> None:
    mock_openai = AsyncMock()
    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_handler.openai",
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
                    deployment_id=deployment_name,
                    api_key=api_key,
                    api_type=api_type,
                    api_base=endpoint,
                    api_version=api_version,
                    input=texts[0:3],
                ),
                call.Embedding.acreate().__getitem__("data"),
                call.Embedding.acreate().__getitem__().__iter__(),
                call.Embedding.acreate(
                    deployment_id=deployment_name,
                    api_key=api_key,
                    api_type=api_type,
                    api_base=endpoint,
                    api_version=api_version,
                    input=texts[3:5],
                ),
            ],
            any_order=False,
        )
