# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock

import pytest
from openai import AsyncOpenAI

from semantic_kernel.connectors.ai.minimax.prompt_execution_settings.minimax_prompt_execution_settings import (
    MiniMaxChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.minimax.services.minimax_handler import MiniMaxHandler
from semantic_kernel.connectors.ai.minimax.services.minimax_model_types import MiniMaxModelTypes


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    return AsyncMock(spec=AsyncOpenAI)


@pytest.fixture
def minimax_handler(mock_openai_client):
    """Create a MiniMaxHandler instance with mocked client."""
    return MiniMaxHandler(
        client=mock_openai_client,
        ai_model_type=MiniMaxModelTypes.CHAT,
        ai_model_id="test-model",
        api_key="test-key",
    )


class TestMiniMaxHandler:
    """Test cases for MiniMaxHandler."""

    def test_init(self, mock_openai_client):
        """Test initialization."""
        handler = MiniMaxHandler(
            client=mock_openai_client,
            ai_model_type=MiniMaxModelTypes.CHAT,
        )

        assert handler.client == mock_openai_client
        assert handler.ai_model_type == MiniMaxModelTypes.CHAT
        assert handler.MODEL_PROVIDER_NAME == "minimax"

    @pytest.mark.asyncio
    async def test_send_chat_completion_request(self, minimax_handler, mock_openai_client):
        """Test sending chat completion request."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(role="assistant", content="Hello!"),
                finish_reason="stop",
            )
        ]
        mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        settings = MiniMaxChatPromptExecutionSettings(
            messages=[{"role": "user", "content": "Hello"}],
            ai_model_id="test-model",
        )

        result = await minimax_handler._send_chat_completion_request(settings)
        assert result == mock_response

        assert minimax_handler.prompt_tokens == 10
        assert minimax_handler.completion_tokens == 20
        assert minimax_handler.total_tokens == 30

    @pytest.mark.asyncio
    async def test_send_request_unsupported_model_type(self, mock_openai_client):
        """Test send_request with unsupported model type."""
        handler = MiniMaxHandler(
            client=mock_openai_client,
            ai_model_type=MiniMaxModelTypes.CHAT,
        )
        object.__setattr__(handler, "ai_model_type", "UNSUPPORTED")

        settings = MiniMaxChatPromptExecutionSettings(
            messages=[{"role": "user", "content": "Hello"}],
            ai_model_id="test-model",
        )

        with pytest.raises(NotImplementedError, match="Model type UNSUPPORTED is not supported"):
            await handler._send_request(settings)
