from unittest.mock import patch

import pytest

from semantic_kernel.connectors.ai.ollama.ollama_prompt_execution_settings import (
    OllamaTextPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.ollama.services.ollama_text_completion import (
    OllamaTextCompletion,
)
from tests.unit.connectors.ollama.utils import MockResponse


def test_settings():
    ollama = OllamaTextCompletion(ai_model_id="test_model")
    settings = ollama.get_prompt_execution_settings_class()
    assert settings == OllamaTextPromptExecutionSettings


@pytest.mark.asyncio
@patch("aiohttp.ClientSession.post")
async def test_complete(mock_post):
    mock_post.return_value = MockResponse(response="test_response")
    ollama = OllamaTextCompletion(ai_model_id="test_model")
    response = await ollama.complete(
        "test prompt",
        OllamaTextPromptExecutionSettings(ai_model_id="test-model", options={"test": "test"}),
    )
    assert response[0].text == "test_response"


@pytest.mark.asyncio
@patch("aiohttp.ClientSession.post")
async def test_complete_stream(mock_post):
    mock_post.return_value = MockResponse(response={"response": "test_response"})
    ollama = OllamaTextCompletion(ai_model_id="test_model")
    response = ollama.complete_stream(
        "test_prompt",
        OllamaTextPromptExecutionSettings(ai_model_id="test_model", options={"test": "test"}),
    )
    async for line in response:
        if line:
            assert line[0].text == "test_response"
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
