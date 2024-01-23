from unittest.mock import patch

import pytest

from semantic_kernel.connectors.ai.ollama.ollama_request_settings import (
    OllamaChatRequestSettings,
)
from semantic_kernel.connectors.ai.ollama.services.ollama_chat_completion import (
    OllamaChatCompletion,
)
from tests.unit.ai.ollama.utils import MockResponse


def test_settings():
    ollama = OllamaChatCompletion(ai_model_id="test_model")
    settings = ollama.get_request_settings_class()
    assert settings == OllamaChatRequestSettings


@pytest.mark.asyncio
@patch("aiohttp.ClientSession.post")
async def test_complete_chat_async(mock_post):
    mock_post.return_value = MockResponse(response={"message": {"content": "test_response"}})
    ollama = OllamaChatCompletion(ai_model_id="test_model")
    response = await ollama.complete_chat_async(
        [{"role": "user", "content": "test_prompt"}],
        OllamaChatRequestSettings(ai_model_id="test_model", options={"test": "test"}),
    )
    assert response == "test_response"
    mock_post.assert_called_once_with(
        "http://localhost:11434/api/chat",
        json={
            "model": "test_model",
            "messages": [{"role": "user", "content": "test_prompt"}],
            "options": {"test": "test"},
            "stream": False,
        },
    )


@pytest.mark.asyncio
@patch("aiohttp.ClientSession.post")
async def test_complete_async(mock_post):
    mock_post.return_value = MockResponse(response={"message": {"content": "test_response"}})
    ollama = OllamaChatCompletion(ai_model_id="test_model")
    response = await ollama.complete_async(
        "test_prompt",
        OllamaChatRequestSettings(ai_model_id="test-model", options={"test": "test"}),
    )
    assert response == "test_response"


@pytest.mark.asyncio
@patch("aiohttp.ClientSession.post")
async def test_complete_chat_stream_async(mock_post):
    mock_post.return_value = MockResponse(response={"message": {"content": "test_response"}})
    ollama = OllamaChatCompletion(ai_model_id="test_model")
    response = ollama.complete_chat_stream_async(
        [{"role": "user", "content": "test_prompt"}],
        OllamaChatRequestSettings(ai_model_id="test_model", options={"test": "test"}),
    )
    async for line in response:
        if line:
            assert line == "test_response"
    mock_post.assert_called_once_with(
        "http://localhost:11434/api/chat",
        json={
            "model": "test_model",
            "messages": [{"role": "user", "content": "test_prompt"}],
            "options": {"test": "test"},
            "stream": True,
        },
    )


@pytest.mark.asyncio
@patch("aiohttp.ClientSession.post")
async def test_complete_stream_async(mock_post):
    mock_post.return_value = MockResponse(response={"message": {"content": "test_response"}})
    ollama = OllamaChatCompletion(ai_model_id="test_model")
    response = ollama.complete_stream_async(
        "test_prompt",
        OllamaChatRequestSettings(ai_model_id="test_model", options={"test": "test"}),
    )
    async for line in response:
        if line:
            assert line == "test_response"
    mock_post.assert_called_once_with(
        "http://localhost:11434/api/chat",
        json={
            "model": "test_model",
            "options": {"test": "test"},
            "stream": True,
            "messages": [{"role": "user", "content": "test_prompt"}],
        },
    )
