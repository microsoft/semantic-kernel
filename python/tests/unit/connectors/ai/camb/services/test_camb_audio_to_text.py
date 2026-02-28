# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock

import pytest

from semantic_kernel.connectors.ai.camb.camb_prompt_execution_settings import CambAudioToTextExecutionSettings
from semantic_kernel.connectors.ai.camb.services.camb_audio_to_text import CambAudioToText
from semantic_kernel.contents.audio_content import AudioContent
from semantic_kernel.exceptions.service_exceptions import (
    ServiceInitializationError,
    ServiceInvalidRequestError,
    ServiceInvalidResponseError,
)


def test_init(camb_unit_test_env):
    mock_client = MagicMock()
    stt = CambAudioToText(async_client=mock_client)
    assert stt.ai_model_id == "camb-transcription"
    assert stt.async_client is mock_client


def test_init_custom_model(camb_unit_test_env):
    mock_client = MagicMock()
    stt = CambAudioToText(ai_model_id="custom-model", async_client=mock_client)
    assert stt.ai_model_id == "custom-model"


def test_init_custom_service_id(camb_unit_test_env):
    mock_client = MagicMock()
    stt = CambAudioToText(service_id="my-stt-service", async_client=mock_client)
    assert stt.service_id == "my-stt-service"


@pytest.mark.parametrize("exclude_list", [["CAMB_API_KEY"]], indirect=True)
def test_init_missing_api_key(camb_unit_test_env):
    with pytest.raises(ServiceInitializationError, match="Failed to create camb.ai settings."):
        CambAudioToText()


def test_prompt_execution_settings_class(camb_unit_test_env):
    mock_client = MagicMock()
    stt = CambAudioToText(async_client=mock_client)
    assert stt.get_prompt_execution_settings_class() == CambAudioToTextExecutionSettings


async def test_get_text_contents(camb_unit_test_env, tmp_path):
    mock_client = MagicMock()

    # Mock create_transcription
    mock_task = MagicMock()
    mock_task.task_id = "task-123"
    mock_client.transcription.create_transcription = AsyncMock(return_value=mock_task)

    # Mock get_transcription_task_status (returns completed immediately)
    mock_status = MagicMock()
    mock_status.status = "SUCCESS"
    mock_status.run_id = "run-456"
    mock_client.transcription.get_transcription_task_status = AsyncMock(return_value=mock_status)

    # Mock get_transcription_result
    mock_result = MagicMock()
    mock_result.text = "Hello from camb.ai transcription!"
    mock_client.transcription.get_transcription_result = AsyncMock(return_value=mock_result)

    stt = CambAudioToText(async_client=mock_client)

    # Create a temporary audio file
    audio_file = tmp_path / "test.wav"
    audio_file.write_bytes(b"fake audio data")

    audio_content = AudioContent(uri=str(audio_file))
    settings = CambAudioToTextExecutionSettings(language=1)

    results = await stt.get_text_contents(audio_content, settings=settings)

    assert len(results) == 1
    assert results[0].text == "Hello from camb.ai transcription!"
    assert results[0].ai_model_id == "camb-transcription"

    mock_client.transcription.create_transcription.assert_awaited_once()
    mock_client.transcription.get_transcription_task_status.assert_awaited_once_with("task-123")
    mock_client.transcription.get_transcription_result.assert_awaited_once_with("run-456")


async def test_get_text_contents_with_bytes(camb_unit_test_env):
    mock_client = MagicMock()

    mock_task = MagicMock()
    mock_task.task_id = "task-789"
    mock_client.transcription.create_transcription = AsyncMock(return_value=mock_task)

    mock_status = MagicMock()
    mock_status.status = "SUCCESS"
    mock_status.run_id = "run-012"
    mock_client.transcription.get_transcription_task_status = AsyncMock(return_value=mock_status)

    mock_result = MagicMock()
    mock_result.text = "Transcribed from bytes"
    mock_client.transcription.get_transcription_result = AsyncMock(return_value=mock_result)

    stt = CambAudioToText(async_client=mock_client)
    audio_content = AudioContent(data=b"raw audio bytes", data_format="base64")

    results = await stt.get_text_contents(audio_content)

    assert len(results) == 1
    assert results[0].text == "Transcribed from bytes"


async def test_get_text_contents_no_audio_data(camb_unit_test_env):
    mock_client = MagicMock()
    stt = CambAudioToText(async_client=mock_client)
    audio_content = AudioContent()

    with pytest.raises(ServiceInvalidRequestError, match="Audio content must have a uri"):
        await stt.get_text_contents(audio_content)


async def test_poll_task_status_failure(camb_unit_test_env):
    mock_client = MagicMock()

    mock_task = MagicMock()
    mock_task.task_id = "task-fail"
    mock_client.transcription.create_transcription = AsyncMock(return_value=mock_task)

    mock_status = MagicMock()
    mock_status.status = "FAILED"
    mock_client.transcription.get_transcription_task_status = AsyncMock(return_value=mock_status)

    stt = CambAudioToText(async_client=mock_client)

    with pytest.raises(ServiceInvalidResponseError, match="task failed"):
        await stt._poll_task_status("task-fail")
