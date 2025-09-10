# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock

import pytest
from openai import AsyncOpenAI

from semantic_kernel.connectors.ai.nvidia.prompt_execution_settings.nvidia_prompt_execution_settings import (
    NvidiaChatPromptExecutionSettings,
    NvidiaEmbeddingPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.nvidia.services.nvidia_handler import NvidiaHandler
from semantic_kernel.connectors.ai.nvidia.services.nvidia_model_types import NvidiaModelTypes


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    return AsyncMock(spec=AsyncOpenAI)


@pytest.fixture
def nvidia_handler(mock_openai_client):
    """Create a NvidiaHandler instance with mocked client."""
    return NvidiaHandler(
        client=mock_openai_client,
        ai_model_type=NvidiaModelTypes.CHAT,
        ai_model_id="test-model",
        api_key="test-key",
    )


class TestNvidiaHandler:
    """Test cases for NvidiaHandler."""

    def test_init(self, mock_openai_client):
        """Test initialization."""
        handler = NvidiaHandler(
            client=mock_openai_client,
            ai_model_type=NvidiaModelTypes.CHAT,
            ai_model_id="test-model",
            api_key="test-key",
        )

        assert handler.client == mock_openai_client
        assert handler.ai_model_type == NvidiaModelTypes.CHAT
        assert handler.ai_model_id == "test-model"
        assert handler.MODEL_PROVIDER_NAME == "nvidia"

    @pytest.mark.asyncio
    async def test_send_chat_completion_request(self, nvidia_handler, mock_openai_client):
        """Test sending chat completion request."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(role="assistant", content="Hello!"),
                finish_reason="stop",
            )
        ]
        mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        mock_openai_client.chat.completions.create.return_value = mock_response

        # Create settings
        settings = NvidiaChatPromptExecutionSettings(
            messages=[{"role": "user", "content": "Hello"}],
            model="test-model",
        )

        # Test the method
        result = await nvidia_handler._send_chat_completion_request(settings)
        assert result == mock_response

        # Verify usage was stored
        assert nvidia_handler.prompt_tokens == 10
        assert nvidia_handler.completion_tokens == 20
        assert nvidia_handler.total_tokens == 30

    @pytest.mark.asyncio
    async def test_send_chat_completion_request_with_nvext(self, nvidia_handler, mock_openai_client):
        """Test sending chat completion request with nvext parameter."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(role="assistant", content='{"result": "success"}'),
                finish_reason="stop",
            )
        ]
        mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        mock_openai_client.chat.completions.create.return_value = mock_response

        # Create settings with nvext
        settings = NvidiaChatPromptExecutionSettings(
            messages=[{"role": "user", "content": "Give me JSON"}],
            model="test-model",
            extra_body={"nvext": {"guided_json": {"type": "object"}}},
        )

        # Test the method
        result = await nvidia_handler._send_chat_completion_request(settings)
        assert result == mock_response

        # Verify the client was called with nvext in extra_body
        call_args = mock_openai_client.chat.completions.create.call_args[1]
        assert "extra_body" in call_args
        assert "nvext" in call_args["extra_body"]
        assert call_args["extra_body"]["nvext"] == {"guided_json": {"type": "object"}}

    @pytest.mark.asyncio
    async def test_send_embedding_request(self, mock_openai_client):
        """Test sending embedding request."""
        handler = NvidiaHandler(
            client=mock_openai_client,
            ai_model_type=NvidiaModelTypes.EMBEDDING,
            ai_model_id="test-model",
        )

        # Mock the response
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=[0.1, 0.2, 0.3]),
            MagicMock(embedding=[0.4, 0.5, 0.6]),
        ]
        mock_response.usage = MagicMock(prompt_tokens=10, total_tokens=10)
        mock_openai_client.embeddings.create.return_value = mock_response

        # Create settings
        settings = NvidiaEmbeddingPromptExecutionSettings(
            input=["hello", "world"],
            model="test-model",
        )

        # Test the method
        result = await handler._send_embedding_request(settings)
        assert result == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]

    @pytest.mark.asyncio
    async def test_send_request_unsupported_model_type(self, nvidia_handler):
        """Test send_request with unsupported model type."""
        nvidia_handler.ai_model_type = "UNSUPPORTED"
        settings = NvidiaChatPromptExecutionSettings(
            messages=[{"role": "user", "content": "Hello"}],
            model="test-model",
        )

        with pytest.raises(NotImplementedError, match="Model type UNSUPPORTED is not supported"):
            await nvidia_handler._send_request(settings)
