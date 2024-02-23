from unittest.mock import patch

import pytest

from semantic_kernel.connectors.ai.ollama.ollama_prompt_execution_settings import (
    OllamaChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.ollama.services.ollama_chat_completion import (
    OllamaChatCompletion,
)
from semantic_kernel.contents.chat_history import ChatHistory
from tests.unit.connectors.ollama.utils import MockResponse


def test_settings():
    ollama = OllamaChatCompletion(ai_model_id="test_model")
    settings = ollama.get_prompt_execution_settings_class()
    assert settings == OllamaChatPromptExecutionSettings


@pytest.mark.asyncio
@patch("aiohttp.ClientSession.post")
async def test_complete_chat(mock_post):
    mock_post.return_value = MockResponse(response={"message": {"content": "test_response"}})
    ollama = OllamaChatCompletion(ai_model_id="test_model")
    chat_history = ChatHistory()
    chat_history.add_user_message("test_prompt")
    response = await ollama.complete_chat(
        chat_history,
        OllamaChatPromptExecutionSettings(service_id="test_model", ai_model_id="test_model", options={"test": "test"}),
    )
    assert response[0].content == "test_response"
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
async def test_complete(mock_post):
    mock_post.return_value = MockResponse(response={"message": {"content": "test_response"}})
    ollama = OllamaChatCompletion(ai_model_id="test_model")
    response = await ollama.complete(
        "test_prompt",
        OllamaChatPromptExecutionSettings(service_id="test_model", ai_model_id="test_model", options={"test": "test"}),
    )
    assert response[0].text == "test_response"


@pytest.mark.asyncio
@patch("aiohttp.ClientSession.post")
async def test_complete_chat_stream(mock_post):
    mock_post.return_value = MockResponse(response={"message": {"content": "test_response"}})
    ollama = OllamaChatCompletion(ai_model_id="test_model")
    chat_history = ChatHistory()
    chat_history.add_user_message("test_prompt")
    response = ollama.complete_chat_stream(
        chat_history,
        OllamaChatPromptExecutionSettings(ai_model_id="test_model", options={"test": "test"}),
    )
    async for line in response:
        if line:
            assert line[0].content == "test_response"
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
async def test_complete_stream(mock_post):
    mock_post.return_value = MockResponse(response={"message": {"content": "test_response"}})
    ollama = OllamaChatCompletion(ai_model_id="test_model")
    response = ollama.complete_stream(
        "test_prompt",
        OllamaChatPromptExecutionSettings(ai_model_id="test_model", options={"test": "test"}),
    )
    async for line in response:
        if line:
            assert line[0].text == "test_response"
    mock_post.assert_called_once_with(
        "http://localhost:11434/api/chat",
        json={
            "model": "test_model",
            "options": {"test": "test"},
            "stream": True,
            "messages": [{"role": "user", "content": "test_prompt"}],
        },
    )
