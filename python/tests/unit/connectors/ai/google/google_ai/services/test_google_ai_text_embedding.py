# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch

import pytest
from google.genai.models import AsyncModels
from google.genai.types import ContentEmbedding, EmbedContentConfigDict, EmbedContentResponse
from numpy import array, ndarray

from semantic_kernel.connectors.ai.google.google_ai.google_ai_prompt_execution_settings import (
    GoogleAIEmbeddingPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.google.google_ai.google_ai_settings import GoogleAISettings
from semantic_kernel.connectors.ai.google.google_ai.services.google_ai_text_embedding import GoogleAITextEmbedding
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError


# region init
def test_google_ai_text_embedding_init(google_ai_unit_test_env) -> None:
    """Test initialization of GoogleAITextEmbedding"""
    model_id = google_ai_unit_test_env["GOOGLE_AI_EMBEDDING_MODEL_ID"]
    api_key = google_ai_unit_test_env["GOOGLE_AI_API_KEY"]
    google_ai_text_embedding = GoogleAITextEmbedding()

    assert google_ai_text_embedding.ai_model_id == model_id
    assert google_ai_text_embedding.service_id == model_id

    assert isinstance(google_ai_text_embedding.service_settings, GoogleAISettings)
    assert google_ai_text_embedding.service_settings.embedding_model_id == model_id
    assert google_ai_text_embedding.service_settings.api_key.get_secret_value() == api_key


def test_google_ai_text_embedding_init_with_service_id(google_ai_unit_test_env, service_id) -> None:
    """Test initialization of GoogleAITextEmbedding with a service_id that is not the model_id"""
    google_ai_text_embedding = GoogleAITextEmbedding(service_id=service_id)

    assert google_ai_text_embedding.service_id == service_id


def test_google_ai_text_embedding_init_with_model_id_in_argument(google_ai_unit_test_env) -> None:
    """Test initialization of GoogleAITextEmbedding with model_id in argument"""
    google_ai_chat_completion = GoogleAITextEmbedding(embedding_model_id="custom_model_id")

    assert google_ai_chat_completion.ai_model_id == "custom_model_id"
    assert google_ai_chat_completion.service_id == "custom_model_id"


@pytest.mark.parametrize("exclude_list", [["GOOGLE_AI_EMBEDDING_MODEL_ID"]], indirect=True)
def test_google_ai_text_embedding_init_with_empty_model_id(google_ai_unit_test_env) -> None:
    """Test initialization of GoogleAITextEmbedding with an empty model_id"""
    with pytest.raises(ServiceInitializationError):
        GoogleAITextEmbedding(env_file_path="fake_env_file_path.env")


@pytest.mark.parametrize("exclude_list", [["GOOGLE_AI_API_KEY"]], indirect=True)
def test_google_ai_text_embedding_init_with_empty_api_key(google_ai_unit_test_env) -> None:
    """Test initialization of GoogleAITextEmbedding with an empty api_key"""
    with pytest.raises(ServiceInitializationError):
        GoogleAITextEmbedding(env_file_path="fake_env_file_path.env")


def test_prompt_execution_settings_class(google_ai_unit_test_env) -> None:
    google_ai_text_embedding = GoogleAITextEmbedding()
    assert google_ai_text_embedding.get_prompt_execution_settings_class() == GoogleAIEmbeddingPromptExecutionSettings


# endregion init


@patch.object(AsyncModels, "embed_content", new_callable=AsyncMock)
async def test_embedding(mock_google_model_embed_content, google_ai_unit_test_env, prompt):
    """Test that the service initializes and generates embeddings correctly."""
    model_id = google_ai_unit_test_env["GOOGLE_AI_EMBEDDING_MODEL_ID"]

    mock_google_model_embed_content.return_value = EmbedContentResponse(
        embeddings=[ContentEmbedding(values=[0.1, 0.2, 0.3])]
    )
    settings = GoogleAIEmbeddingPromptExecutionSettings()

    google_ai_text_embedding = GoogleAITextEmbedding()
    response: ndarray = await google_ai_text_embedding.generate_embeddings(
        [prompt],
        settings=settings,
    )

    assert len(response) == 1
    assert response.all() == array([0.1, 0.2, 0.3]).all()
    mock_google_model_embed_content.assert_called_once_with(
        model=model_id,
        contents=[prompt],
        config=EmbedContentConfigDict(**settings.prepare_settings_dict()),
    )


@patch.object(AsyncModels, "embed_content", new_callable=AsyncMock)
async def test_embedding_with_settings(mock_google_model_embed_content, google_ai_unit_test_env, prompt):
    """Test that the service initializes and generates embeddings correctly."""
    model_id = google_ai_unit_test_env["GOOGLE_AI_EMBEDDING_MODEL_ID"]

    mock_google_model_embed_content.return_value = EmbedContentResponse(
        embeddings=[ContentEmbedding(values=[0.1, 0.2, 0.3])]
    )
    settings = GoogleAIEmbeddingPromptExecutionSettings()
    settings.output_dimensionality = 3

    google_ai_text_embedding = GoogleAITextEmbedding()
    response: ndarray = await google_ai_text_embedding.generate_embeddings(
        [prompt],
        settings=settings,
    )

    assert len(response) == 1
    assert response.all() == array([0.1, 0.2, 0.3]).all()
    mock_google_model_embed_content.assert_called_once_with(
        model=model_id,
        contents=[prompt],
        config=EmbedContentConfigDict(**settings.prepare_settings_dict()),
    )


@patch.object(AsyncModels, "embed_content", new_callable=AsyncMock)
async def test_embedding_without_settings(mock_google_model_embed_content, google_ai_unit_test_env, prompt):
    """Test that the service initializes and generates embeddings correctly without settings."""
    model_id = google_ai_unit_test_env["GOOGLE_AI_EMBEDDING_MODEL_ID"]

    mock_google_model_embed_content.return_value = EmbedContentResponse(
        embeddings=[ContentEmbedding(values=[0.1, 0.2, 0.3])]
    )
    google_ai_text_embedding = GoogleAITextEmbedding()
    response: ndarray = await google_ai_text_embedding.generate_embeddings([prompt])

    assert len(response) == 1
    assert response.all() == array([0.1, 0.2, 0.3]).all()
    mock_google_model_embed_content.assert_called_once_with(
        model=model_id,
        contents=[prompt],
        config=EmbedContentConfigDict(),
    )


@patch.object(AsyncModels, "embed_content", new_callable=AsyncMock)
async def test_embedding_list_input(mock_google_model_embed_content, google_ai_unit_test_env, prompt):
    """Test that the service initializes and generates embeddings correctly with a list of prompts."""
    model_id = google_ai_unit_test_env["GOOGLE_AI_EMBEDDING_MODEL_ID"]

    mock_google_model_embed_content.return_value = EmbedContentResponse(
        embeddings=[ContentEmbedding(values=[0.1, 0.2, 0.3]), ContentEmbedding(values=[0.1, 0.2, 0.3])]
    )
    settings = GoogleAIEmbeddingPromptExecutionSettings()

    google_ai_text_embedding = GoogleAITextEmbedding()
    response: ndarray = await google_ai_text_embedding.generate_embeddings(
        [prompt, prompt],
        settings=settings,
    )

    assert len(response) == 2
    assert response.all() == array([[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]]).all()
    mock_google_model_embed_content.assert_called_once_with(
        model=model_id,
        contents=[prompt, prompt],
        config=EmbedContentConfigDict(),
    )


@patch.object(AsyncModels, "embed_content", new_callable=AsyncMock)
async def test_raw_embedding(mock_google_model_embed_content, google_ai_unit_test_env, prompt):
    """Test that the service initializes and generates embeddings correctly."""
    model_id = google_ai_unit_test_env["GOOGLE_AI_EMBEDDING_MODEL_ID"]

    mock_google_model_embed_content.return_value = EmbedContentResponse(
        embeddings=[ContentEmbedding(values=[0.1, 0.2, 0.3])]
    )
    settings = GoogleAIEmbeddingPromptExecutionSettings()

    google_ai_text_embedding = GoogleAITextEmbedding()
    response: list[list[float]] = await google_ai_text_embedding.generate_raw_embeddings(
        [prompt],
        settings=settings,
    )

    assert len(response) == 1
    assert response[0] == [0.1, 0.2, 0.3]
    mock_google_model_embed_content.assert_called_once_with(
        model=model_id,
        contents=[prompt],
        config=EmbedContentConfigDict(**settings.prepare_settings_dict()),
    )
