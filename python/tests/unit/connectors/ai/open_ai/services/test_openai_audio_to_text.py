# Copyright (c) Microsoft. All rights reserved.


import os
from unittest.mock import AsyncMock, patch

import pytest
from openai import AsyncClient
from openai.resources.audio.transcriptions import AsyncTranscriptions
from openai.types.audio import Transcription

from semantic_kernel.connectors.ai.open_ai import OpenAIAudioToTextExecutionSettings
from semantic_kernel.connectors.ai.open_ai.services.open_ai_audio_to_text import OpenAIAudioToText
from semantic_kernel.contents import AudioContent
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError, ServiceInvalidRequestError


def test_init(openai_unit_test_env):
    openai_audio_to_text = OpenAIAudioToText()

    assert openai_audio_to_text.client is not None
    assert isinstance(openai_audio_to_text.client, AsyncClient)
    assert openai_audio_to_text.ai_model_id == openai_unit_test_env["OPENAI_AUDIO_TO_TEXT_MODEL_ID"]


def test_init_validation_fail() -> None:
    with pytest.raises(ServiceInitializationError, match="Failed to create OpenAI settings."):
        OpenAIAudioToText(api_key="34523", ai_model_id={"test": "dict"})


@pytest.mark.parametrize("exclude_list", [["OPENAI_AUDIO_TO_TEXT_MODEL_ID"]], indirect=True)
def test_init_audio_to_text_model_not_provided(openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError, match="The OpenAI audio to text model ID is required."):
        OpenAIAudioToText(
            env_file_path="test.env",
        )


@pytest.mark.parametrize("exclude_list", [["OPENAI_API_KEY"]], indirect=True)
def test_init_with_empty_api_key(openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        OpenAIAudioToText(
            env_file_path="test.env",
        )


def test_init_to_from_dict(openai_unit_test_env):
    default_headers = {"X-Unit-Test": "test-guid"}

    settings = {
        "ai_model_id": openai_unit_test_env["OPENAI_AUDIO_TO_TEXT_MODEL_ID"],
        "api_key": openai_unit_test_env["OPENAI_API_KEY"],
        "default_headers": default_headers,
    }
    audio_to_text = OpenAIAudioToText.from_dict(settings)
    dumped_settings = audio_to_text.to_dict()
    assert dumped_settings["ai_model_id"] == settings["ai_model_id"]
    assert dumped_settings["api_key"] == settings["api_key"]


def test_prompt_execution_settings_class(openai_unit_test_env) -> None:
    openai_audio_to_text = OpenAIAudioToText()
    assert openai_audio_to_text.get_prompt_execution_settings_class() == OpenAIAudioToTextExecutionSettings


async def test_get_text_contents(openai_unit_test_env):
    audio_content = AudioContent.from_audio_file(
        os.path.join(os.path.dirname(__file__), "../../../../../", "assets/sample_audio.mp3")
    )

    with patch.object(AsyncTranscriptions, "create", new_callable=AsyncMock) as mock_transcription_create:
        mock_transcription_create.return_value = Transcription(text="This is a test audio file.")

        openai_audio_to_text = OpenAIAudioToText()

        text_contents = await openai_audio_to_text.get_text_contents(audio_content)
        assert len(text_contents) == 1
        assert text_contents[0].text == "This is a test audio file."
        assert text_contents[0].ai_model_id == openai_unit_test_env["OPENAI_AUDIO_TO_TEXT_MODEL_ID"]


async def test_get_text_contents_invalid_audio_content(openai_unit_test_env):
    audio_content = AudioContent()

    openai_audio_to_text = OpenAIAudioToText()
    with pytest.raises(ServiceInvalidRequestError, match="Audio content uri must be a string to a local file."):
        await openai_audio_to_text.get_text_contents(audio_content)
