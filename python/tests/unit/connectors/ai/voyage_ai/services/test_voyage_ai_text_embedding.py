# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock

import pytest
from numpy import ndarray

from semantic_kernel.connectors.ai.voyage_ai import (
    VoyageAIEmbeddingPromptExecutionSettings,
    VoyageAITextEmbedding,
)
from semantic_kernel.exceptions.service_exceptions import ServiceResponseException


def test_init(voyage_ai_unit_test_env):
    """Test VoyageAI text embedding initialization."""
    embedding_service = VoyageAITextEmbedding(
        ai_model_id="voyage-3-large",
        api_key="test-api-key",
    )

    assert embedding_service.ai_model_id == "voyage-3-large"
    assert embedding_service.service_id == "voyage-3-large"
    assert embedding_service.aclient is not None


def test_init_with_service_id(voyage_ai_unit_test_env):
    """Test initialization with custom service ID."""
    embedding_service = VoyageAITextEmbedding(
        ai_model_id="voyage-3-large",
        service_id="custom-service",
        api_key="test-api-key",
    )

    assert embedding_service.ai_model_id == "voyage-3-large"
    assert embedding_service.service_id == "custom-service"


def test_init_from_env(voyage_ai_unit_test_env):
    """Test initialization from environment variables."""
    embedding_service = VoyageAITextEmbedding(
        ai_model_id="voyage-3-large",
    )

    assert embedding_service.ai_model_id == "voyage-3-large"


def test_init_with_custom_endpoint(voyage_ai_unit_test_env):
    """Test initialization with custom endpoint."""
    custom_endpoint = "https://custom-endpoint.com/v1"
    embedding_service = VoyageAITextEmbedding(
        ai_model_id="voyage-3-large",
        api_key="test-api-key",
        endpoint=custom_endpoint,
    )

    assert embedding_service.endpoint == custom_endpoint


def test_prompt_execution_settings_class():
    """Test getting prompt execution settings class."""
    embedding_service = VoyageAITextEmbedding(
        ai_model_id="voyage-3-large",
        api_key="test-api-key",
    )

    assert embedding_service.get_prompt_execution_settings_class() == VoyageAIEmbeddingPromptExecutionSettings


@pytest.mark.asyncio
async def test_generate_embeddings(voyage_ai_unit_test_env):
    """Test generating embeddings."""
    # Mock response
    mock_response = MagicMock()
    mock_response.embeddings = [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
    ]

    embedding_service = VoyageAITextEmbedding(
        ai_model_id="voyage-3-large",
        api_key="test-api-key",
    )

    # Mock the aclient
    embedding_service._aclient.embed = AsyncMock(return_value=mock_response)

    texts = ["hello world", "goodbye world"]
    embeddings = await embedding_service.generate_embeddings(texts)

    assert isinstance(embeddings, ndarray)
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 3
    embedding_service._aclient.embed.assert_called_once()


@pytest.mark.asyncio
async def test_generate_embeddings_with_settings(voyage_ai_unit_test_env):
    """Test generating embeddings with execution settings."""
    # Mock response
    mock_response = MagicMock()
    mock_response.embeddings = [[0.1, 0.2, 0.3]]

    embedding_service = VoyageAITextEmbedding(
        ai_model_id="voyage-3-large",
        api_key="test-api-key",
    )

    # Mock the aclient
    embedding_service._aclient.embed = AsyncMock(return_value=mock_response)

    settings = VoyageAIEmbeddingPromptExecutionSettings(
        input_type="query",
        truncation=True,
        output_dimension=1024,
    )

    texts = ["test text"]
    embeddings = await embedding_service.generate_embeddings(texts, settings=settings)

    assert isinstance(embeddings, ndarray)
    embedding_service._aclient.embed.assert_called_once()


@pytest.mark.asyncio
async def test_generate_embeddings_with_different_output_dtype(voyage_ai_unit_test_env):
    """Test generating embeddings with different output dtype."""
    # Mock response
    mock_response = MagicMock()
    mock_response.embeddings = [[1, 2, 3]]  # int8 format

    embedding_service = VoyageAITextEmbedding(
        ai_model_id="voyage-3-large",
        api_key="test-api-key",
    )

    # Mock the aclient
    embedding_service._aclient.embed = AsyncMock(return_value=mock_response)

    settings = VoyageAIEmbeddingPromptExecutionSettings(
        output_dtype="int8",
    )

    texts = ["test text"]
    embeddings = await embedding_service.generate_embeddings(texts, settings=settings)

    assert isinstance(embeddings, ndarray)
    embedding_service._aclient.embed.assert_called_once()


@pytest.mark.asyncio
async def test_generate_embeddings_failure(voyage_ai_unit_test_env):
    """Test handling of embedding generation failure."""
    embedding_service = VoyageAITextEmbedding(
        ai_model_id="voyage-3-large",
        api_key="test-api-key",
    )

    # Mock the aclient to raise an exception
    embedding_service._aclient.embed = AsyncMock(side_effect=Exception("API error"))

    texts = ["test text"]

    with pytest.raises(ServiceResponseException):
        await embedding_service.generate_embeddings(texts)


def test_service_url():
    """Test service URL retrieval."""
    embedding_service = VoyageAITextEmbedding(
        ai_model_id="voyage-3-large",
        api_key="test-api-key",
    )

    assert embedding_service.service_url() == "https://api.voyageai.com/v1"


def test_service_url_with_custom_endpoint():
    """Test service URL with custom endpoint."""
    custom_endpoint = "https://custom.api.com/v1"
    embedding_service = VoyageAITextEmbedding(
        ai_model_id="voyage-3-large",
        api_key="test-api-key",
        endpoint=custom_endpoint,
    )

    assert embedding_service.service_url() == custom_endpoint
