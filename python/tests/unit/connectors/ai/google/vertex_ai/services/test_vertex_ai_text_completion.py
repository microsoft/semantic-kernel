# Copyright (c) Microsoft. All rights reserved.


from unittest.mock import AsyncMock, patch

import pytest
from vertexai.generative_models import GenerativeModel

from semantic_kernel.connectors.ai.google.vertex_ai.services.vertex_ai_text_completion import VertexAITextCompletion
from semantic_kernel.connectors.ai.google.vertex_ai.vertex_ai_prompt_execution_settings import (
    VertexAITextPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.google.vertex_ai.vertex_ai_settings import VertexAISettings
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError


# region init
def test_vertex_ai_text_completion_init(vertex_ai_unit_test_env) -> None:
    """Test initialization of VertexAITextCompletion"""
    model_id = vertex_ai_unit_test_env["VERTEX_AI_GEMINI_MODEL_ID"]
    project_id = vertex_ai_unit_test_env["VERTEX_AI_PROJECT_ID"]
    vertex_ai_text_completion = VertexAITextCompletion()

    assert vertex_ai_text_completion.ai_model_id == model_id
    assert vertex_ai_text_completion.service_id == model_id

    assert isinstance(vertex_ai_text_completion.service_settings, VertexAISettings)
    assert vertex_ai_text_completion.service_settings.gemini_model_id == model_id
    assert vertex_ai_text_completion.service_settings.project_id == project_id


def test_vertex_ai_text_completion_init_with_service_id(vertex_ai_unit_test_env, service_id) -> None:
    """Test initialization of VertexAITextCompletion with a service id that is not the model id"""
    vertex_ai_text_completion = VertexAITextCompletion(service_id=service_id)

    assert vertex_ai_text_completion.service_id == service_id


def test_vertex_ai_text_completion_init_with_model_id_in_argument(vertex_ai_unit_test_env) -> None:
    """Test initialization of VertexAIChatCompletion with model id in argument"""
    vertex_ai_text_completion = VertexAITextCompletion(gemini_model_id="custom_model_id")

    assert vertex_ai_text_completion.ai_model_id == "custom_model_id"
    assert vertex_ai_text_completion.service_id == "custom_model_id"


@pytest.mark.parametrize("exclude_list", [["VERTEX_AI_GEMINI_MODEL_ID"]], indirect=True)
def test_vertex_ai_text_completion_init_with_empty_model_id(vertex_ai_unit_test_env) -> None:
    """Test initialization of VertexAITextCompletion with an empty model id"""
    with pytest.raises(ServiceInitializationError):
        VertexAITextCompletion(env_file_path="fake_env_file_path.env")


@pytest.mark.parametrize("exclude_list", [["VERTEX_AI_PROJECT_ID"]], indirect=True)
def test_vertex_ai_text_completion_init_with_empty_project_id(vertex_ai_unit_test_env) -> None:
    """Test initialization of VertexAITextCompletion with an empty project id"""
    with pytest.raises(ServiceInitializationError):
        VertexAITextCompletion(env_file_path="fake_env_file_path.env")


def test_prompt_execution_settings_class(vertex_ai_unit_test_env) -> None:
    vertex_ai_text_completion = VertexAITextCompletion()
    assert vertex_ai_text_completion.get_prompt_execution_settings_class() == VertexAITextPromptExecutionSettings


# endregion init


# region text completion


@patch.object(GenerativeModel, "generate_content_async", new_callable=AsyncMock)
async def test_vertex_ai_text_completion(
    mock_vertex_ai_model_generate_content_async,
    vertex_ai_unit_test_env,
    prompt: str,
    mock_vertex_ai_text_completion_response,
) -> None:
    """Test text completion with VertexAITextCompletion"""
    settings = VertexAITextPromptExecutionSettings()

    mock_vertex_ai_model_generate_content_async.return_value = mock_vertex_ai_text_completion_response

    vertex_ai_text_completion = VertexAITextCompletion()
    responses: list[TextContent] = await vertex_ai_text_completion.get_text_contents(prompt, settings)

    mock_vertex_ai_model_generate_content_async.assert_called_once_with(
        contents=prompt,
        generation_config=settings.prepare_settings_dict(),
    )
    assert len(responses) == 1
    assert responses[0].text == mock_vertex_ai_text_completion_response.candidates[0].content.parts[0].text
    assert "usage" in responses[0].metadata
    assert "prompt_feedback" in responses[0].metadata
    assert responses[0].inner_content == mock_vertex_ai_text_completion_response


# endregion text completion


# region streaming text completion


@patch.object(GenerativeModel, "generate_content_async", new_callable=AsyncMock)
async def test_vertex_ai_streaming_text_completion(
    mock_vertex_ai_model_generate_content_async,
    vertex_ai_unit_test_env,
    prompt: str,
    mock_vertex_ai_streaming_text_completion_response,
) -> None:
    """Test streaming text completion with VertexAITextCompletion"""
    settings = VertexAITextPromptExecutionSettings()

    mock_vertex_ai_model_generate_content_async.return_value = mock_vertex_ai_streaming_text_completion_response

    vertex_ai_text_completion = VertexAITextCompletion()
    async for chunks in vertex_ai_text_completion.get_streaming_text_contents(prompt, settings):
        assert len(chunks) == 1
        assert "usage" in chunks[0].metadata
        assert "prompt_feedback" in chunks[0].metadata

    mock_vertex_ai_model_generate_content_async.assert_called_once_with(
        contents=prompt,
        generation_config=settings.prepare_settings_dict(),
        stream=True,
    )


# endregion streaming text completion
