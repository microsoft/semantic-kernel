# Copyright (c) Microsoft. All rights reserved.


from unittest.mock import patch

import httpx
import pytest
from openai import AsyncClient, _legacy_response
from openai.resources.audio.speech import AsyncSpeech

from semantic_kernel.connectors.ai.open_ai import OpenAITextToAudio, OpenAITextToAudioExecutionSettings
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError


def test_init(openai_unit_test_env):
    openai_text_to_audio = OpenAITextToAudio()

    assert openai_text_to_audio.client is not None
    assert isinstance(openai_text_to_audio.client, AsyncClient)
    assert openai_text_to_audio.ai_model_id == openai_unit_test_env["OPENAI_TEXT_TO_AUDIO_MODEL_ID"]


def test_init_validation_fail() -> None:
    with pytest.raises(ServiceInitializationError, match="Failed to create OpenAI settings."):
        OpenAITextToAudio(api_key="34523", ai_model_id={"test": "dict"})


@pytest.mark.parametrize("exclude_list", [["OPENAI_TEXT_TO_AUDIO_MODEL_ID"]], indirect=True)
def test_init_text_to_audio_model_not_provided(openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError, match="The OpenAI text to audio model ID is required."):
        OpenAITextToAudio(
            env_file_path="test.env",
        )


@pytest.mark.parametrize("exclude_list", [["OPENAI_API_KEY"]], indirect=True)
def test_init_with_empty_api_key(openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        OpenAITextToAudio(
            env_file_path="test.env",
        )


def test_init_to_from_dict(openai_unit_test_env):
    default_headers = {"X-Unit-Test": "test-guid"}

    settings = {
        "ai_model_id": openai_unit_test_env["OPENAI_TEXT_TO_AUDIO_MODEL_ID"],
        "api_key": openai_unit_test_env["OPENAI_API_KEY"],
        "default_headers": default_headers,
    }
    audio_to_text = OpenAITextToAudio.from_dict(settings)
    dumped_settings = audio_to_text.to_dict()
    assert dumped_settings["ai_model_id"] == settings["ai_model_id"]
    assert dumped_settings["api_key"] == settings["api_key"]


def test_prompt_execution_settings_class(openai_unit_test_env) -> None:
    openai_text_to_audio = OpenAITextToAudio()
    assert openai_text_to_audio.get_prompt_execution_settings_class() == OpenAITextToAudioExecutionSettings


@patch.object(AsyncSpeech, "create", return_value=_legacy_response.HttpxBinaryResponseContent(httpx.Response(200)))
async def test_get_text_contents(mock_speech_create, openai_unit_test_env):
    openai_text_to_audio = OpenAITextToAudio()

    audio_contents = await openai_text_to_audio.get_audio_contents("Hello World!")
    assert len(audio_contents) == 1
    assert audio_contents[0].ai_model_id == openai_unit_test_env["OPENAI_TEXT_TO_AUDIO_MODEL_ID"]
