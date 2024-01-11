from unittest.mock import patch

import pytest

from semantic_kernel.connectors.ai.ollama.ollama_request_settings import OllamaTextRequestSettings
from semantic_kernel.connectors.ai.ollama.services.ollama_text_completion import OllamaTextCompletion
from tests.unit.ai.ollama.utils import MockResponse


def test_settings():
    ollama = OllamaTextCompletion(ai_model_id="test_model")
    settings = ollama.get_request_settings_class()
    assert settings == OllamaTextRequestSettings


@pytest.mark.asyncio
@patch("aiohttp.ClientSession.post")
async def test_complete_async(mock_post):
    mock_post.return_value = MockResponse(response="test_response")
    ollama = OllamaTextCompletion(ai_model_id="test_model")
    response = await ollama.complete_async(
        "test_prompt",
        OllamaTextRequestSettings(ai_model_id="test-model", options={"test": "test"}),
    )
    assert response == "test_response"


@pytest.mark.asyncio
@patch("aiohttp.ClientSession.post")
async def test_complete_stream_async(mock_post):
    mock_post.return_value = MockResponse(response={"response": "test_response"})
    ollama = OllamaTextCompletion(ai_model_id="test_model")
    response = ollama.complete_stream_async(
        "test_prompt",
        OllamaTextRequestSettings(ai_model_id="test_model", options={"test": "test"}),
    )
    async for line in response:
        if line:
            assert line == "test_response"
    mock_post.assert_called_once_with(
        "http://localhost:11434/api/generate",
        json={
            "model": "test_model",
            "options": {"test": "test"},
            "stream": True,
            "prompt": "test_prompt",
            "raw": False,
        },
    )
