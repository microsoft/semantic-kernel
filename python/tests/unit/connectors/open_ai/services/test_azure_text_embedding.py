# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, call, patch

import pytest
from openai import AsyncAzureOpenAI
from openai.resources.embeddings import AsyncEmbeddings
from pydantic import ValidationError

from semantic_kernel.connectors.ai.ai_exception import AIException
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

    # Test successful initialization
    azure_text_embedding = AzureTextEmbedding(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
    )

    assert azure_text_embedding.client is not None
    assert isinstance(azure_text_embedding.client, AsyncAzureOpenAI)
    assert azure_text_embedding.ai_model_id == deployment_name
    assert isinstance(azure_text_embedding, EmbeddingGeneratorBase)


def test_azure_text_embedding_init_with_empty_deployment_name() -> None:
    # deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"

    with pytest.raises(ValidationError, match="ai_model_id"):
        AzureTextEmbedding(
            deployment_name="",
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
        )


def test_azure_text_embedding_init_with_empty_api_key() -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    # api_key = "test_api_key"
    api_version = "2023-03-15-preview"

    with pytest.raises(AIException, match="api_key"):
        AzureTextEmbedding(
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key="",
            api_version=api_version,
        )


def test_azure_text_embedding_init_with_empty_endpoint() -> None:
    deployment_name = "test_deployment"
    # endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"

    with pytest.raises(ValidationError, match="endpoint"):
        AzureTextEmbedding(
            deployment_name=deployment_name,
            endpoint="",
            api_key=api_key,
            api_version=api_version,
        )


def test_azure_text_embedding_init_with_invalid_endpoint() -> None:
    deployment_name = "test_deployment"
    endpoint = "http://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"

    with pytest.raises(ValidationError, match="https"):
        AzureTextEmbedding(
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
        )


def test_azure_text_embedding_init_with_from_dict() -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    default_headers = {"test_header": "test_value"}

    settings = {
        "deployment_name": deployment_name,
        "endpoint": endpoint,
        "api_key": api_key,
        "api_version": api_version,
        "default_headers": default_headers,
    }

    azure_text_embedding = AzureTextEmbedding.from_dict(settings=settings)

    assert azure_text_embedding.client is not None
    assert isinstance(azure_text_embedding.client, AsyncAzureOpenAI)
    assert azure_text_embedding.ai_model_id == deployment_name
    assert isinstance(azure_text_embedding, EmbeddingGeneratorBase)
    assert endpoint in str(azure_text_embedding.client.base_url)
    assert azure_text_embedding.client.api_key == api_key

    # Assert that the default header we added is present in the client's default headers
    for key, value in default_headers.items():
        assert key in azure_text_embedding.client.default_headers
        assert azure_text_embedding.client.default_headers[key] == value


@pytest.mark.asyncio
@patch.object(AsyncEmbeddings, "create", new_callable=AsyncMock)
async def test_azure_text_embedding_calls_with_parameters(mock_create) -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    texts = ["hello world", "goodbye world"]

    azure_text_embedding = AzureTextEmbedding(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
    )

    await azure_text_embedding.generate_embeddings(texts)

    mock_create.assert_awaited_once_with(
        input=texts,
        model=deployment_name,
    )


@pytest.mark.asyncio
@patch.object(AsyncEmbeddings, "create", new_callable=AsyncMock)
async def test_azure_text_embedding_calls_with_batches(mock_create) -> None:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    texts = [i for i in range(0, 5)]

    azure_text_embedding = AzureTextEmbedding(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
    )

    await azure_text_embedding.generate_embeddings(texts, batch_size=3)

    mock_create.assert_has_awaits(
        [
            call(
                model=deployment_name,
                input=texts[0:3],
            ),
            call(
                model=deployment_name,
                input=texts[3:5],
            ),
        ],
        any_order=False,
    )
