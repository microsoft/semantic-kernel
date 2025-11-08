# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock

import pytest
from numpy import ndarray

from semantic_kernel.connectors.ai.voyage_ai import (
    VoyageAIMultimodalEmbedding,
    VoyageAIMultimodalEmbeddingPromptExecutionSettings,
)
from semantic_kernel.exceptions.service_exceptions import ServiceResponseException


def test_init(voyage_ai_unit_test_env):
    """Test VoyageAI multimodal embedding initialization."""
    embedding_service = VoyageAIMultimodalEmbedding(
        ai_model_id="voyage-multimodal-3",
        api_key="test-api-key",
    )

    assert embedding_service.ai_model_id == "voyage-multimodal-3"
    assert embedding_service.aclient is not None


def test_init_default_model(voyage_ai_unit_test_env):
    """Test initialization with default model from env."""
    embedding_service = VoyageAIMultimodalEmbedding(
        api_key="test-api-key",
    )

    # Should use default model
    assert embedding_service.ai_model_id is not None


def test_prompt_execution_settings_class():
    """Test getting prompt execution settings class."""
    embedding_service = VoyageAIMultimodalEmbedding(
        ai_model_id="voyage-multimodal-3",
        api_key="test-api-key",
    )

    assert embedding_service.get_prompt_execution_settings_class() == VoyageAIMultimodalEmbeddingPromptExecutionSettings


@pytest.mark.asyncio
async def test_generate_multimodal_embeddings(voyage_ai_unit_test_env):
    """Test generating multimodal embeddings."""
    # Mock response
    mock_response = MagicMock()
    mock_response.embeddings = [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
    ]

    embedding_service = VoyageAIMultimodalEmbedding(
        ai_model_id="voyage-multimodal-3",
        api_key="test-api-key",
    )

    # Mock the aclient
    embedding_service._aclient.multimodal_embed = AsyncMock(return_value=mock_response)

    # Text-only inputs
    inputs = ["text1", "text2"]
    embeddings = await embedding_service.generate_multimodal_embeddings(inputs)

    assert isinstance(embeddings, ndarray)
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 3
    embedding_service._aclient.multimodal_embed.assert_called_once()


@pytest.mark.asyncio
async def test_generate_embeddings_wrapper(voyage_ai_unit_test_env):
    """Test the generate_embeddings wrapper method."""
    # Mock response
    mock_response = MagicMock()
    mock_response.embeddings = [[0.1, 0.2, 0.3]]

    embedding_service = VoyageAIMultimodalEmbedding(
        ai_model_id="voyage-multimodal-3",
        api_key="test-api-key",
    )

    # Mock the aclient
    embedding_service._aclient.multimodal_embed = AsyncMock(return_value=mock_response)

    texts = ["test text"]
    embeddings = await embedding_service.generate_embeddings(texts)

    assert isinstance(embeddings, ndarray)
    embedding_service._aclient.multimodal_embed.assert_called_once()


@pytest.mark.asyncio
async def test_generate_multimodal_embeddings_with_settings(voyage_ai_unit_test_env):
    """Test generating multimodal embeddings with settings."""
    # Mock response
    mock_response = MagicMock()
    mock_response.embeddings = [[0.1, 0.2]]

    embedding_service = VoyageAIMultimodalEmbedding(
        ai_model_id="voyage-multimodal-3",
        api_key="test-api-key",
    )

    # Mock the aclient
    embedding_service._aclient.multimodal_embed = AsyncMock(return_value=mock_response)

    settings = VoyageAIMultimodalEmbeddingPromptExecutionSettings(
        input_type="query",
        truncation=True,
    )

    inputs = ["text input"]
    embeddings = await embedding_service.generate_multimodal_embeddings(inputs, settings=settings)

    assert isinstance(embeddings, ndarray)
    embedding_service._aclient.multimodal_embed.assert_called_once()


@pytest.mark.asyncio
async def test_generate_multimodal_embeddings_mixed_inputs(voyage_ai_unit_test_env):
    """Test generating embeddings with mixed text and mock image inputs."""
    # Mock response
    mock_response = MagicMock()
    mock_response.embeddings = [
        [0.1, 0.2, 0.3],
        [0.4, 0.5, 0.6],
    ]

    embedding_service = VoyageAIMultimodalEmbedding(
        ai_model_id="voyage-multimodal-3",
        api_key="test-api-key",
    )

    # Mock the aclient
    embedding_service._aclient.multimodal_embed = AsyncMock(return_value=mock_response)

    # Mixed inputs (mock)
    mock_image = MagicMock()  # Mock PIL Image
    inputs = [
        "text description",
        mock_image,
    ]

    embeddings = await embedding_service.generate_multimodal_embeddings(inputs)

    assert isinstance(embeddings, ndarray)
    assert len(embeddings) == 2
    embedding_service._aclient.multimodal_embed.assert_called_once()


@pytest.mark.asyncio
async def test_generate_multimodal_embeddings_failure(voyage_ai_unit_test_env):
    """Test handling of failure."""
    embedding_service = VoyageAIMultimodalEmbedding(
        ai_model_id="voyage-multimodal-3",
        api_key="test-api-key",
    )

    # Mock the aclient to raise an exception
    embedding_service._aclient.multimodal_embed = AsyncMock(side_effect=Exception("API error"))

    inputs = ["text"]

    with pytest.raises(ServiceResponseException):
        await embedding_service.generate_multimodal_embeddings(inputs)
