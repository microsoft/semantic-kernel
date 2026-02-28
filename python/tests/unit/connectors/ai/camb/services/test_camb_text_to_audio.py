# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import MagicMock, patch

import pytest

from semantic_kernel.connectors.ai.camb.camb_prompt_execution_settings import CambTextToAudioExecutionSettings
from semantic_kernel.connectors.ai.camb.services.camb_text_to_audio import CambTextToAudio
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError


def test_init(camb_unit_test_env):
    mock_client = MagicMock()
    tts = CambTextToAudio(async_client=mock_client)
    assert tts.ai_model_id == "mars-flash"
    assert tts.async_client is mock_client


def test_init_custom_model(camb_unit_test_env):
    mock_client = MagicMock()
    tts = CambTextToAudio(ai_model_id="mars-pro", async_client=mock_client)
    assert tts.ai_model_id == "mars-pro"


def test_init_custom_service_id(camb_unit_test_env):
    mock_client = MagicMock()
    tts = CambTextToAudio(service_id="my-tts-service", async_client=mock_client)
    assert tts.service_id == "my-tts-service"


@pytest.mark.parametrize("exclude_list", [["CAMB_API_KEY"]], indirect=True)
def test_init_missing_api_key(camb_unit_test_env):
    with pytest.raises(ServiceInitializationError, match="Failed to create camb.ai settings."):
        CambTextToAudio()


def test_prompt_execution_settings_class(camb_unit_test_env):
    mock_client = MagicMock()
    tts = CambTextToAudio(async_client=mock_client)
    assert tts.get_prompt_execution_settings_class() == CambTextToAudioExecutionSettings


async def test_get_audio_contents(camb_unit_test_env):
    mock_client = MagicMock()

    async def mock_tts(**kwargs):
        yield b"audio_chunk_1"
        yield b"audio_chunk_2"

    mock_client.text_to_speech.tts = mock_tts

    tts = CambTextToAudio(async_client=mock_client)
    settings = CambTextToAudioExecutionSettings(voice_id=147320, language="en-us")

    results = await tts.get_audio_contents("Hello World!", settings=settings)

    assert len(results) == 1
    assert results[0].ai_model_id == "mars-flash"
    assert results[0].mime_type == "audio/wav"


async def test_get_audio_contents_default_settings(camb_unit_test_env):
    mock_client = MagicMock()

    async def mock_tts(**kwargs):
        yield b"audio_data"

    mock_client.text_to_speech.tts = mock_tts

    tts = CambTextToAudio(async_client=mock_client)

    results = await tts.get_audio_contents("Hello World!")

    assert len(results) == 1
    assert results[0].ai_model_id == "mars-flash"


async def test_get_audio_contents_mp3_format(camb_unit_test_env):
    mock_client = MagicMock()

    async def mock_tts(**kwargs):
        yield b"mp3_data"

    mock_client.text_to_speech.tts = mock_tts

    tts = CambTextToAudio(async_client=mock_client)
    settings = CambTextToAudioExecutionSettings(output_format="mp3")

    results = await tts.get_audio_contents("Hello!", settings=settings)

    assert results[0].mime_type == "audio/mpeg"
