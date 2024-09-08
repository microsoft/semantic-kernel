# Copyright (c) Microsoft. All rights reserved.


from unittest.mock import AsyncMock, patch

import pytest
from numpy import array, ndarray
from vertexai.language_models import TextEmbedding, TextEmbeddingModel

from semantic_kernel.connectors.ai.google.vertex_ai.services.vertex_ai_text_embedding import (
    VertexAITextEmbedding,
)
from semantic_kernel.connectors.ai.google.vertex_ai.vertex_ai_prompt_execution_settings import (
    VertexAIEmbeddingPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.google.vertex_ai.vertex_ai_settings import (
    VertexAISettings,
)
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError
from tests.unit.connectors.google.vertex_ai.conftest import MockTextEmbeddingModel


# region init
def test_vertex_ai_text_embedding_init(vertex_ai_unit_test_env) -> None:
    """Test initialization of VertexAITextEmbedding"""
    model_id = vertex_ai_unit_test_env["VERTEX_AI_EMBEDDING_MODEL_ID"]
    project_id = vertex_ai_unit_test_env["VERTEX_AI_PROJECT_ID"]
    vertex_ai_text_embedding = VertexAITextEmbedding()

    assert vertex_ai_text_embedding.ai_model_id == model_id
    assert vertex_ai_text_embedding.service_id == model_id

    assert isinstance(vertex_ai_text_embedding.service_settings, VertexAISettings)
    assert vertex_ai_text_embedding.service_settings.embedding_model_id == model_id
    assert vertex_ai_text_embedding.service_settings.project_id == project_id


def test_vertex_ai_text_embedding_init_with_service_id(
    vertex_ai_unit_test_env, service_id
) -> None:
    """Test initialization of VertexAITextEmbedding with a service id that is not the model id"""
    vertex_ai_text_embedding = VertexAITextEmbedding(service_id=service_id)

    assert vertex_ai_text_embedding.service_id == service_id


def test_vertex_ai_text_embedding_init_with_model_id_in_argument(
    vertex_ai_unit_test_env,
) -> None:
    """Test initialization of VertexAITextEmbedding with model id in argument"""
    vertex_ai_chat_completion = VertexAITextEmbedding(
        embedding_model_id="custom_model_id"
    )

    assert vertex_ai_chat_completion.ai_model_id == "custom_model_id"
    assert vertex_ai_chat_completion.service_id == "custom_model_id"


@pytest.mark.parametrize(
    "exclude_list", [["VERTEX_AI_EMBEDDING_MODEL_ID"]], indirect=True
)
def test_vertex_ai_text_embedding_init_with_empty_model_id(
    vertex_ai_unit_test_env,
) -> None:
    """Test initialization of VertexAITextEmbedding with an empty model id"""
    with pytest.raises(ServiceInitializationError):
        VertexAITextEmbedding(env_file_path="fake_env_file_path.env")


@pytest.mark.parametrize("exclude_list", [["VERTEX_AI_PROJECT_ID"]], indirect=True)
def test_vertex_ai_text_embedding_init_with_empty_project_id(
    vertex_ai_unit_test_env,
) -> None:
    """Test initialization of VertexAITextEmbedding with an empty project id"""
    with pytest.raises(ServiceInitializationError):
        VertexAITextEmbedding(env_file_path="fake_env_file_path.env")


def test_prompt_execution_settings_class(vertex_ai_unit_test_env) -> None:
    vertex_ai_text_embedding = VertexAITextEmbedding()
    assert (
        vertex_ai_text_embedding.get_prompt_execution_settings_class()
        == VertexAIEmbeddingPromptExecutionSettings
    )


# endregion init


@pytest.mark.asyncio
@patch.object(TextEmbeddingModel, "from_pretrained")
@patch.object(MockTextEmbeddingModel, "get_embeddings_async", new_callable=AsyncMock)
async def test_embedding(
    mock_embedding_client, mock_from_pretrained, vertex_ai_unit_test_env, prompt
):
    """Test that the service initializes and generates embeddings correctly."""
    mock_from_pretrained.return_value = MockTextEmbeddingModel()
    mock_embedding_client.return_value = [TextEmbedding(values=[0.1, 0.2, 0.3])]

    settings = VertexAIEmbeddingPromptExecutionSettings()

    vertex_ai_text_embedding = VertexAITextEmbedding()
    response: ndarray = await vertex_ai_text_embedding.generate_embeddings(
        [prompt],
        settings=settings,
    )

    assert len(response) == 1
    assert response.all() == array([0.1, 0.2, 0.3]).all()
    mock_embedding_client.assert_called_once_with([prompt])


@pytest.mark.asyncio
@patch.object(TextEmbeddingModel, "from_pretrained")
@patch.object(MockTextEmbeddingModel, "get_embeddings_async", new_callable=AsyncMock)
async def test_embedding_with_settings(
    mock_embedding_client, mock_from_pretrained, vertex_ai_unit_test_env, prompt
):
    """Test that the service initializes and generates embeddings correctly."""
    mock_from_pretrained.return_value = MockTextEmbeddingModel()
    mock_embedding_client.return_value = [TextEmbedding(values=[0.1, 0.2, 0.3])]

    settings = VertexAIEmbeddingPromptExecutionSettings()
    settings.output_dimensionality = 3
    settings.auto_truncate = True

    vertex_ai_text_embedding = VertexAITextEmbedding()
    response: ndarray = await vertex_ai_text_embedding.generate_embeddings(
        [prompt],
        settings=settings,
    )

    assert len(response) == 1
    assert response.all() == array([0.1, 0.2, 0.3]).all()
    mock_embedding_client.assert_called_once_with(
        [prompt],
        **settings.prepare_settings_dict(),
    )


@pytest.mark.asyncio
@patch.object(TextEmbeddingModel, "from_pretrained")
@patch.object(MockTextEmbeddingModel, "get_embeddings_async", new_callable=AsyncMock)
async def test_embedding_without_settings(
    mock_embedding_client, mock_from_pretrained, vertex_ai_unit_test_env, prompt
):
    """Test that the service initializes and generates embeddings correctly without settings."""
    mock_from_pretrained.return_value = MockTextEmbeddingModel()
    mock_embedding_client.return_value = [TextEmbedding(values=[0.1, 0.2, 0.3])]

    vertex_ai_text_embedding = VertexAITextEmbedding()
    response: ndarray = await vertex_ai_text_embedding.generate_embeddings([prompt])

    assert len(response) == 1
    assert response.all() == array([0.1, 0.2, 0.3]).all()
    mock_embedding_client.assert_called_once_with([prompt])


@pytest.mark.asyncio
@patch.object(TextEmbeddingModel, "from_pretrained")
@patch.object(MockTextEmbeddingModel, "get_embeddings_async", new_callable=AsyncMock)
async def test_embedding_list_input(
    mock_embedding_client, mock_from_pretrained, vertex_ai_unit_test_env, prompt
):
    """Test that the service initializes and generates embeddings correctly with a list of prompts."""
    mock_from_pretrained.return_value = MockTextEmbeddingModel()
    mock_embedding_client.return_value = [
        TextEmbedding(values=[0.1, 0.2, 0.3]),
        TextEmbedding(values=[0.1, 0.2, 0.3]),
    ]

    vertex_ai_text_embedding = VertexAITextEmbedding()
    response: ndarray = await vertex_ai_text_embedding.generate_embeddings(
        [prompt, prompt]
    )

    assert len(response) == 2
    assert response.all() == array([[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]]).all()
    mock_embedding_client.assert_called_once_with([prompt, prompt])


@pytest.mark.asyncio
@patch.object(TextEmbeddingModel, "from_pretrained")
@patch.object(MockTextEmbeddingModel, "get_embeddings_async", new_callable=AsyncMock)
async def test_raw_embedding(
    mock_embedding_client, mock_from_pretrained, vertex_ai_unit_test_env, prompt
):
    """Test that the service initializes and generates embeddings correctly."""
    mock_from_pretrained.return_value = MockTextEmbeddingModel()
    mock_embedding_client.return_value = [TextEmbedding(values=[0.1, 0.2, 0.3])]

    settings = VertexAIEmbeddingPromptExecutionSettings()

    vertex_ai_text_embedding = VertexAITextEmbedding()
    response: ndarray = await vertex_ai_text_embedding.generate_raw_embeddings(
        [prompt], settings
    )

    assert len(response) == 1
    assert response[0] == [0.1, 0.2, 0.3]
    mock_embedding_client.assert_called_once_with([prompt])
