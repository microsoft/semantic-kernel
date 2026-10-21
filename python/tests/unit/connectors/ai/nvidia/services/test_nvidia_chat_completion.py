# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch

import pytest
from openai.resources.chat.completions import AsyncCompletions
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from openai.types.completion_usage import CompletionUsage
from pydantic import BaseModel

from semantic_kernel.connectors.ai.nvidia import NvidiaChatCompletion
from semantic_kernel.connectors.ai.nvidia.prompt_execution_settings.nvidia_prompt_execution_settings import (
    NvidiaChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.nvidia.services.nvidia_chat_completion import DEFAULT_NVIDIA_CHAT_MODEL
from semantic_kernel.contents import ChatHistory
from semantic_kernel.exceptions import ServiceInitializationError, ServiceResponseException


@pytest.fixture
def nvidia_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for NvidiaChatCompletion."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {"NVIDIA_API_KEY": "test_api_key", "NVIDIA_CHAT_MODEL_ID": "meta/llama-3.1-8b-instruct"}

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
        model="meta/llama-3.1-8b-instruct",
        object="chat.completion",
        usage=usage,
    )


class TestNvidiaChatCompletion:
    """Test cases for NvidiaChatCompletion."""

    def test_init_with_defaults(self, nvidia_unit_test_env):
        """Test initialization with default values."""
        service = NvidiaChatCompletion()
        assert service.ai_model_id == nvidia_unit_test_env["NVIDIA_CHAT_MODEL_ID"]

    def test_get_prompt_execution_settings_class(self, nvidia_unit_test_env):
        """Test getting the prompt execution settings class."""
        service = NvidiaChatCompletion()
        from semantic_kernel.connectors.ai.nvidia.prompt_execution_settings.nvidia_prompt_execution_settings import (
            NvidiaChatPromptExecutionSettings,
        )

        assert service.get_prompt_execution_settings_class() == NvidiaChatPromptExecutionSettings

    @pytest.mark.parametrize("exclude_list", [["NVIDIA_API_KEY"]], indirect=True)
    def test_init_with_empty_api_key(self, nvidia_unit_test_env):
        """Test initialization fails with empty API key."""
        with pytest.raises(ServiceInitializationError):
            NvidiaChatCompletion()

    @pytest.mark.parametrize("exclude_list", [["NVIDIA_CHAT_MODEL_ID"]], indirect=True)
    def test_init_with_empty_model_id(self, nvidia_unit_test_env):
        """Test initialization with empty model ID uses default."""
        service = NvidiaChatCompletion()
        assert service.ai_model_id == DEFAULT_NVIDIA_CHAT_MODEL

    def test_init_with_custom_model_id(self, nvidia_unit_test_env):
        """Test initialization with custom model ID."""
        custom_model = "custom/nvidia-model"
        service = NvidiaChatCompletion(ai_model_id=custom_model)
        assert service.ai_model_id == custom_model

    @pytest.mark.asyncio
    @patch.object(AsyncCompletions, "create", new_callable=AsyncMock)
    async def test_get_chat_message_contents(self, mock_create, nvidia_unit_test_env):
        """Test basic chat completion."""
        mock_create.return_value = _create_mock_chat_completion("Hello!")

        service = NvidiaChatCompletion()
        chat_history = ChatHistory()
        chat_history.add_user_message("Hello")
        settings = NvidiaChatPromptExecutionSettings()

        result = await service.get_chat_message_contents(chat_history, settings)

        assert len(result) == 1
        assert result[0].content == "Hello!"

    @pytest.mark.asyncio
    @patch.object(AsyncCompletions, "create", new_callable=AsyncMock)
    async def test_structured_output_with_pydantic_model(self, mock_create, nvidia_unit_test_env):
        """Test structured output with Pydantic model."""

        # Define test model
        class TestModel(BaseModel):
            name: str
            value: int

        mock_create.return_value = _create_mock_chat_completion('{"name": "test", "value": 42}')

        service = NvidiaChatCompletion()
        chat_history = ChatHistory()
        chat_history.add_user_message("Give me structured data")
        settings = NvidiaChatPromptExecutionSettings()
        settings.response_format = TestModel

        await service.get_chat_message_contents(chat_history, settings)

        # Verify nvext was passed
        call_args = mock_create.call_args[1]
        assert "extra_body" in call_args
        assert "nvext" in call_args["extra_body"]
        assert "guided_json" in call_args["extra_body"]["nvext"]

    @pytest.mark.asyncio
    @patch.object(AsyncCompletions, "create", new_callable=AsyncMock)
    async def test_error_handling(self, mock_create, nvidia_unit_test_env):
        """Test error handling."""
        mock_create.side_effect = Exception("API Error")

        service = NvidiaChatCompletion()
        chat_history = ChatHistory()
        chat_history.add_user_message("Hello")
        settings = NvidiaChatPromptExecutionSettings()

        with pytest.raises(ServiceResponseException):
            await service.get_chat_message_contents(chat_history, settings)
