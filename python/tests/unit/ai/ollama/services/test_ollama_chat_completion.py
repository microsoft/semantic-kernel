from unittest.mock import MagicMock, patch

import pytest

from semantic_kernel.connectors.ai.ollama.ollama_request_settings import OllamaChatRequestSettings
from semantic_kernel.connectors.ai.ollama.services.ollama_chat_completion import OllamaChatCompletion


@pytest.fixture
def mock_session():
    with patch("aiohttp.ClientSession.get", new_callable=MagicMock) as mock_get:
        mock_get.return_value.__aenter__.return_value.json = MagicMock(return_value={"response": "test_response"})
        yield mock_get


class MockResponse:
    def __init__(self, response, status=200):
        self._response = response
        self.status = status

    async def text(self):
        return self._response

    async def json(self):
        return self._response

    def raise_for_status(self):
        pass

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def __aenter__(self):
        return self


@pytest.mark.asyncio
@patch("aiohttp.ClientSession.post")
async def test_complete_chat_async(mock_post):
    mock_post.return_value = MockResponse(response={"message": {"content": "test_response"}})
    ollama = OllamaChatCompletion(ai_model_id="test_model")
    response = await ollama.complete_chat_async(
        [{"role": "user", "message": "test_prompt"}],
        OllamaChatRequestSettings(ai_model_id="test-model", options={"test": "test"}),
    )
    assert response == "test_response"


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
