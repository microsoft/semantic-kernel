# Copyright (c) Microsoft. All rights reserved.

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from semantic_kernel.connectors.ai.camb.camb_plugin import CambPlugin
from semantic_kernel.exceptions import FunctionExecutionException


@pytest.fixture()
def mock_async_client():
    return MagicMock()


@pytest.fixture()
def plugin(mock_async_client):
    return CambPlugin(async_client=mock_async_client)


def test_init_with_client(mock_async_client):
    plugin = CambPlugin(async_client=mock_async_client)
    assert plugin.async_client is mock_async_client


def test_init_with_api_key(monkeypatch):
    monkeypatch.setenv("CAMB_API_KEY", "test-key")
    mock_client_cls = MagicMock()
    mock_client_cls.return_value = MagicMock()
    with patch.dict("sys.modules", {"camb": MagicMock(), "camb.client": MagicMock(AsyncCambAI=mock_client_cls)}):
        plugin = CambPlugin()
        mock_client_cls.assert_called_once_with(api_key="test-key")


def test_init_missing_api_key(monkeypatch):
    monkeypatch.delenv("CAMB_API_KEY", raising=False)
    with pytest.raises(FunctionExecutionException, match="API key is required"):
        CambPlugin()


async def test_translate(plugin, mock_async_client):
    mock_async_client.translation.translation_stream = AsyncMock(return_value="Hola mundo")

    result = await plugin.translate(text="Hello world", source_language=1, target_language=2)

    assert result == "Hola mundo"
    mock_async_client.translation.translation_stream.assert_awaited_once()


async def test_translate_with_formality(plugin, mock_async_client):
    mock_async_client.translation.translation_stream = AsyncMock(return_value="Buenos dias")

    result = await plugin.translate(text="Good morning", source_language=1, target_language=2, formality=1)

    assert result == "Buenos dias"
    call_kwargs = mock_async_client.translation.translation_stream.call_args[1]
    assert call_kwargs["formality"] == 1


async def test_translate_api_error_200(plugin, mock_async_client):
    """Test handling of SDK bug where 200 responses raise ApiError."""

    class MockApiError(Exception):
        def __init__(self, status_code, body):
            self.status_code = status_code
            self.body = body
            super().__init__(f"ApiError {status_code}")

    error = MockApiError(status_code=200, body="Translated text from error body")
    mock_async_client.translation.translation_stream = AsyncMock(side_effect=error)

    result = await plugin.translate(text="Hello", source_language=1, target_language=2)

    assert result == "Translated text from error body"


async def test_translated_tts(plugin, mock_async_client):
    import httpx

    mock_task = MagicMock()
    mock_task.task_id = "task-tts-1"
    mock_async_client.translated_tts.create_translated_tts = AsyncMock(return_value=mock_task)

    mock_status = MagicMock()
    mock_status.status = "SUCCESS"
    mock_status.run_id = "run-tts-1"
    mock_async_client.translated_tts.get_translated_tts_task_status = AsyncMock(return_value=mock_status)

    mock_async_client._api_key = "test-key"

    mock_response = MagicMock()
    mock_response.content = b"fake-audio-data"
    mock_response.headers = {"content-type": "audio/wav"}
    mock_response.raise_for_status = MagicMock()

    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(return_value=mock_response)
    mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_http_client.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_http_client):
        result = await plugin.translated_tts(
            text="Hello", source_language=1, target_language=2, voice_id=147320
        )

    parsed = json.loads(result)
    assert "audio_base64" in parsed
    assert parsed["content_type"] == "audio/wav"
    assert parsed["run_id"] == "run-tts-1"


async def test_clone_voice(plugin, mock_async_client, tmp_path):
    mock_result = MagicMock()
    mock_result.voice_id = 12345
    mock_result.voice_name = "My Voice"
    mock_result.status = "created"
    mock_async_client.voice_cloning.create_custom_voice = AsyncMock(return_value=mock_result)

    audio_file = tmp_path / "sample.wav"
    audio_file.write_bytes(b"fake audio for cloning")

    result = await plugin.clone_voice(
        voice_name="My Voice", audio_file_path=str(audio_file), gender=1
    )

    parsed = json.loads(result)
    assert parsed["voice_id"] == 12345
    assert parsed["voice_name"] == "My Voice"
    assert parsed["status"] == "created"


async def test_list_voices(plugin, mock_async_client):
    mock_voice1 = {"id": 1, "voice_name": "Voice A", "gender": "male", "age": 30, "language": "en-us"}
    mock_voice2 = {"id": 2, "voice_name": "Voice B", "gender": "female", "age": 25, "language": "es-es"}

    mock_async_client.voice_cloning.list_voices = AsyncMock(return_value=[mock_voice1, mock_voice2])

    result = await plugin.list_voices()

    parsed = json.loads(result)
    assert len(parsed) == 2
    assert parsed[0]["name"] == "Voice A"
    assert parsed[1]["name"] == "Voice B"


async def test_text_to_sound(plugin, mock_async_client):
    mock_task = MagicMock()
    mock_task.task_id = "task-sound-1"
    mock_async_client.text_to_audio.create_text_to_audio = AsyncMock(return_value=mock_task)

    mock_status = MagicMock()
    mock_status.status = "SUCCESS"
    mock_status.run_id = "run-sound-1"
    mock_async_client.text_to_audio.get_text_to_audio_status = AsyncMock(return_value=mock_status)

    async def mock_stream(run_id):
        yield b"sound-chunk-1"
        yield b"sound-chunk-2"

    mock_async_client.text_to_audio.get_text_to_audio_result = mock_stream

    result = await plugin.text_to_sound(prompt="A thunderstorm in the distance")

    parsed = json.loads(result)
    assert "audio_base64" in parsed
    assert parsed["run_id"] == "run-sound-1"


async def test_separate_audio(plugin, mock_async_client, tmp_path):
    mock_task = MagicMock()
    mock_task.task_id = "task-sep-1"
    mock_async_client.audio_separation.create_audio_separation = AsyncMock(return_value=mock_task)

    mock_status = MagicMock()
    mock_status.status = "SUCCESS"
    mock_status.run_id = "run-sep-1"
    mock_async_client.audio_separation.get_audio_separation_status = AsyncMock(return_value=mock_status)

    mock_result = MagicMock()
    mock_result.vocals_url = "https://example.com/vocals.wav"
    mock_result.background_url = "https://example.com/background.wav"
    mock_async_client.audio_separation.get_audio_separation_run_info = AsyncMock(return_value=mock_result)

    audio_file = tmp_path / "mixed.wav"
    audio_file.write_bytes(b"mixed audio data")

    result = await plugin.separate_audio(audio_file_path=str(audio_file))

    parsed = json.loads(result)
    assert parsed["vocals_url"] == "https://example.com/vocals.wav"
    assert parsed["background_url"] == "https://example.com/background.wav"
    assert parsed["run_id"] == "run-sep-1"


async def test_poll_task_status_timeout(plugin):
    mock_status = MagicMock()
    mock_status.status = "PENDING"

    mock_get_status = AsyncMock(return_value=mock_status)

    with patch("semantic_kernel.connectors.ai.camb.camb_plugin._MAX_POLL_ATTEMPTS", 2):
        with patch("semantic_kernel.connectors.ai.camb.camb_plugin._POLL_INTERVAL_SECONDS", 0.01):
            with pytest.raises(FunctionExecutionException, match="timed out"):
                await plugin._poll_task_status(mock_get_status, "task-timeout")


async def test_poll_task_status_failure(plugin):
    mock_status = MagicMock()
    mock_status.status = "FAILED"

    mock_get_status = AsyncMock(return_value=mock_status)

    with pytest.raises(FunctionExecutionException, match="task failed"):
        await plugin._poll_task_status(mock_get_status, "task-fail")
