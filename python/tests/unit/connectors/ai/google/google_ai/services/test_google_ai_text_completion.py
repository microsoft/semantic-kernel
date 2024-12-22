# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch

import pytest
from google.generativeai import GenerativeModel
from google.generativeai.types import GenerationConfig

from semantic_kernel.connectors.ai.google.google_ai.google_ai_prompt_execution_settings import (
    GoogleAITextPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.google.google_ai.google_ai_settings import GoogleAISettings
from semantic_kernel.connectors.ai.google.google_ai.services.google_ai_text_completion import GoogleAITextCompletion
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError


# region init
def test_google_ai_text_completion_init(google_ai_unit_test_env) -> None:
    """Test initialization of GoogleAITextCompletion"""
    model_id = google_ai_unit_test_env["GOOGLE_AI_GEMINI_MODEL_ID"]
    api_key = google_ai_unit_test_env["GOOGLE_AI_API_KEY"]
    google_ai_text_completion = GoogleAITextCompletion()

    assert google_ai_text_completion.ai_model_id == model_id
    assert google_ai_text_completion.service_id == model_id

    assert isinstance(google_ai_text_completion.service_settings, GoogleAISettings)
    assert google_ai_text_completion.service_settings.gemini_model_id == model_id
    assert google_ai_text_completion.service_settings.api_key.get_secret_value() == api_key


def test_google_ai_text_completion_init_with_service_id(google_ai_unit_test_env, service_id) -> None:
    """Test initialization of GoogleAITextCompletion with a service_id that is not the model_id"""
    google_ai_text_completion = GoogleAITextCompletion(service_id=service_id)

    assert google_ai_text_completion.service_id == service_id


def test_google_ai_text_completion_init_with_model_id_in_argument(google_ai_unit_test_env) -> None:
    """Test initialization of GoogleAIChatCompletion with model_id in argument"""
    google_ai_text_completion = GoogleAITextCompletion(gemini_model_id="custom_model_id")

    assert google_ai_text_completion.ai_model_id == "custom_model_id"
    assert google_ai_text_completion.service_id == "custom_model_id"


@pytest.mark.parametrize("exclude_list", [["GOOGLE_AI_GEMINI_MODEL_ID"]], indirect=True)
def test_google_ai_text_completion_init_with_empty_model_id(google_ai_unit_test_env) -> None:
    """Test initialization of GoogleAITextCompletion with an empty model_id"""
    with pytest.raises(ServiceInitializationError):
        GoogleAITextCompletion(env_file_path="fake_env_file_path.env")


@pytest.mark.parametrize("exclude_list", [["GOOGLE_AI_API_KEY"]], indirect=True)
def test_google_ai_text_completion_init_with_empty_api_key(google_ai_unit_test_env) -> None:
    """Test initialization of GoogleAITextCompletion with an empty api_key"""
    with pytest.raises(ServiceInitializationError):
        GoogleAITextCompletion(env_file_path="fake_env_file_path.env")


def test_prompt_execution_settings_class(google_ai_unit_test_env) -> None:
    google_ai_text_completion = GoogleAITextCompletion()
    assert google_ai_text_completion.get_prompt_execution_settings_class() == GoogleAITextPromptExecutionSettings


# endregion init


# region text completion


@patch.object(GenerativeModel, "generate_content_async", new_callable=AsyncMock)
async def test_google_ai_text_completion(
    mock_google_model_generate_content_async,
    google_ai_unit_test_env,
    prompt: str,
    mock_google_ai_text_completion_response,
) -> None:
    """Test text completion with GoogleAITextCompletion"""
    settings = GoogleAITextPromptExecutionSettings()

    mock_google_model_generate_content_async.return_value = mock_google_ai_text_completion_response

    google_ai_text_completion = GoogleAITextCompletion()
    responses: list[TextContent] = await google_ai_text_completion.get_text_contents(prompt, settings)

    mock_google_model_generate_content_async.assert_called_once_with(
        contents=prompt,
        generation_config=GenerationConfig(**settings.prepare_settings_dict()),
    )
    assert len(responses) == 1
    assert responses[0].text == mock_google_ai_text_completion_response.candidates[0].content.parts[0].text
    assert "usage" in responses[0].metadata
    assert "prompt_feedback" in responses[0].metadata
    assert responses[0].inner_content == mock_google_ai_text_completion_response


# endregion text completion


# region streaming text completion


@patch.object(GenerativeModel, "generate_content_async", new_callable=AsyncMock)
async def test_google_ai_streaming_text_completion(
    mock_google_model_generate_content_async,
    google_ai_unit_test_env,
    prompt: str,
    mock_google_ai_streaming_text_completion_response,
) -> None:
    """Test streaming text completion with GoogleAITextCompletion"""
    settings = GoogleAITextPromptExecutionSettings()

    mock_google_model_generate_content_async.return_value = mock_google_ai_streaming_text_completion_response

    google_ai_text_completion = GoogleAITextCompletion()
    async for chunks in google_ai_text_completion.get_streaming_text_contents(prompt, settings):
        assert len(chunks) == 1
        assert "usage" in chunks[0].metadata
        assert "prompt_feedback" in chunks[0].metadata

    mock_google_model_generate_content_async.assert_called_once_with(
        contents=prompt,
        generation_config=GenerationConfig(**settings.prepare_settings_dict()),
        stream=True,
    )


# endregion streaming text completion
