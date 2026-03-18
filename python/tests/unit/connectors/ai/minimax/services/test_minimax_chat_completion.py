# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch

import pytest
from openai.resources.chat.completions import AsyncCompletions
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from openai.types.completion_usage import CompletionUsage

from semantic_kernel.connectors.ai.minimax import MiniMaxChatCompletion
from semantic_kernel.connectors.ai.minimax.prompt_execution_settings.minimax_prompt_execution_settings import (
    MiniMaxChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.minimax.services.minimax_chat_completion import DEFAULT_MINIMAX_CHAT_MODEL
from semantic_kernel.contents import ChatHistory
from semantic_kernel.exceptions import ServiceInitializationError, ServiceResponseException


@pytest.fixture
def minimax_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for MiniMaxChatCompletion."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {"MINIMAX_API_KEY": "test_api_key", "MINIMAX_CHAT_MODEL_ID": "MiniMax-M2.7"}

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


def _create_mock_chat_completion(content: str = "Hello!") -> ChatCompletion:
    """Helper function to create a mock ChatCompletion response."""
    message = ChatCompletionMessage(role="assistant", content=content)
    choice = Choice(
        finish_reason="stop",
        index=0,
        message=message,
    )
    usage = CompletionUsage(completion_tokens=20, prompt_tokens=10, total_tokens=30)
    return ChatCompletion(
        id="test-id",
        choices=[choice],
        created=1234567890,
        model="MiniMax-M2.7",
        object="chat.completion",
        usage=usage,
    )


class TestMiniMaxChatCompletion:
    """Test cases for MiniMaxChatCompletion."""

    def test_init_with_defaults(self, minimax_unit_test_env):
        """Test initialization with default values."""
        service = MiniMaxChatCompletion()
        assert service.ai_model_id == minimax_unit_test_env["MINIMAX_CHAT_MODEL_ID"]

    def test_get_prompt_execution_settings_class(self, minimax_unit_test_env):
        """Test getting the prompt execution settings class."""
        service = MiniMaxChatCompletion()
        assert service.get_prompt_execution_settings_class() == MiniMaxChatPromptExecutionSettings

    @pytest.mark.parametrize("exclude_list", [["MINIMAX_API_KEY"]], indirect=True)
    def test_init_with_empty_api_key(self, minimax_unit_test_env):
        """Test initialization fails with empty API key."""
        with pytest.raises(ServiceInitializationError):
            MiniMaxChatCompletion()

    @pytest.mark.parametrize("exclude_list", [["MINIMAX_CHAT_MODEL_ID"]], indirect=True)
    def test_init_with_empty_model_id(self, minimax_unit_test_env):
        """Test initialization with empty model ID uses default."""
        service = MiniMaxChatCompletion()
        assert service.ai_model_id == DEFAULT_MINIMAX_CHAT_MODEL

    def test_init_with_custom_model_id(self, minimax_unit_test_env):
        """Test initialization with custom model ID."""
        custom_model = "MiniMax-M2.7-highspeed"
        service = MiniMaxChatCompletion(ai_model_id=custom_model)
        assert service.ai_model_id == custom_model

    @pytest.mark.asyncio
    @patch.object(AsyncCompletions, "create", new_callable=AsyncMock)
    async def test_get_chat_message_contents(self, mock_create, minimax_unit_test_env):
        """Test basic chat completion."""
        mock_create.return_value = _create_mock_chat_completion("Hello!")

        service = MiniMaxChatCompletion()
        chat_history = ChatHistory()
        chat_history.add_user_message("Hello")
        settings = MiniMaxChatPromptExecutionSettings()

        result = await service.get_chat_message_contents(chat_history, settings)

        assert len(result) == 1
        assert result[0].content == "Hello!"

    @pytest.mark.asyncio
    @patch.object(AsyncCompletions, "create", new_callable=AsyncMock)
    async def test_error_handling(self, mock_create, minimax_unit_test_env):
        """Test error handling."""
        mock_create.side_effect = Exception("API Error")

        service = MiniMaxChatCompletion()
        chat_history = ChatHistory()
        chat_history.add_user_message("Hello")
        settings = MiniMaxChatPromptExecutionSettings()

        with pytest.raises(ServiceResponseException):
            await service.get_chat_message_contents(chat_history, settings)
