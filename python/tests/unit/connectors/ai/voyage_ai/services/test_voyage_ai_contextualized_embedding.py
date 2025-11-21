# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock

import pytest
from numpy import ndarray

from semantic_kernel.connectors.ai.voyage_ai import (
    VoyageAIContextualizedEmbedding,
    VoyageAIContextualizedEmbeddingPromptExecutionSettings,
)
from semantic_kernel.exceptions.service_exceptions import ServiceResponseException


def test_init(voyage_ai_unit_test_env):
    """Test VoyageAI contextualized embedding initialization."""
    embedding_service = VoyageAIContextualizedEmbedding(
        ai_model_id="voyage-context-3",
        api_key="test-api-key",
    )

    assert embedding_service.ai_model_id == "voyage-context-3"
    assert embedding_service.aclient is not None


def test_init_default_model(voyage_ai_unit_test_env):
    """Test initialization with default model from env."""
    embedding_service = VoyageAIContextualizedEmbedding(
        api_key="test-api-key",
    )

    # Should use default model
    assert embedding_service.ai_model_id is not None


def test_prompt_execution_settings_class():
    """Test getting prompt execution settings class."""
    embedding_service = VoyageAIContextualizedEmbedding(
        ai_model_id="voyage-context-3",
        api_key="test-api-key",
    )

    assert (
        embedding_service.get_prompt_execution_settings_class()
        == VoyageAIContextualizedEmbeddingPromptExecutionSettings
    )


@pytest.mark.asyncio
async def test_generate_contextualized_embeddings(voyage_ai_unit_test_env):
    """Test generating contextualized embeddings."""
    # Mock response - result.embeddings is now a list of arrays directly
    mock_result = MagicMock()
    mock_result.embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]

    mock_response = MagicMock()
    mock_response.results = [mock_result]

    embedding_service = VoyageAIContextualizedEmbedding(
        ai_model_id="voyage-context-3",
        api_key="test-api-key",
    )

    # Mock the aclient
    embedding_service._aclient.contextualized_embed = AsyncMock(return_value=mock_response)

    inputs = [["chunk1", "chunk2"]]
    embeddings = await embedding_service.generate_contextualized_embeddings(inputs)

    assert isinstance(embeddings, ndarray)
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 3
    embedding_service._aclient.contextualized_embed.assert_called_once()


@pytest.mark.asyncio
async def test_generate_embeddings_wrapper(voyage_ai_unit_test_env):
    """Test the generate_embeddings wrapper method."""
    # Mock response - result.embeddings is now a list of arrays directly
    mock_result = MagicMock()
    mock_result.embeddings = [[0.1, 0.2, 0.3]]

    mock_response = MagicMock()
    mock_response.results = [mock_result]

    embedding_service = VoyageAIContextualizedEmbedding(
        ai_model_id="voyage-context-3",
        api_key="test-api-key",
    )

    # Mock the aclient
    embedding_service._aclient.contextualized_embed = AsyncMock(return_value=mock_response)

    texts = ["test text"]
    embeddings = await embedding_service.generate_embeddings(texts)

    assert isinstance(embeddings, ndarray)
    embedding_service._aclient.contextualized_embed.assert_called_once()


@pytest.mark.asyncio
async def test_generate_contextualized_embeddings_with_settings(voyage_ai_unit_test_env):
    """Test generating contextualized embeddings with settings."""
    # Mock response - result.embeddings is now a list of arrays directly
    mock_result = MagicMock()
    mock_result.embeddings = [[0.1, 0.2]]

    mock_response = MagicMock()
    mock_response.results = [mock_result]

    embedding_service = VoyageAIContextualizedEmbedding(
        ai_model_id="voyage-context-3",
        api_key="test-api-key",
    )

    # Mock the aclient
    embedding_service._aclient.contextualized_embed = AsyncMock(return_value=mock_response)

    settings = VoyageAIContextualizedEmbeddingPromptExecutionSettings(
        input_type="document",
    )

    inputs = [["chunk1"]]
    embeddings = await embedding_service.generate_contextualized_embeddings(inputs, settings=settings)

    assert isinstance(embeddings, ndarray)
    embedding_service._aclient.contextualized_embed.assert_called_once()


@pytest.mark.asyncio
async def test_generate_contextualized_embeddings_failure(voyage_ai_unit_test_env):
    """Test handling of failure."""
    embedding_service = VoyageAIContextualizedEmbedding(
        ai_model_id="voyage-context-3",
        api_key="test-api-key",
    )

    # Mock the aclient to raise an exception
    embedding_service._aclient.contextualized_embed = AsyncMock(side_effect=Exception("API error"))

    inputs = [["chunk1"]]

    with pytest.raises(ServiceResponseException):
        await embedding_service.generate_contextualized_embeddings(inputs)
