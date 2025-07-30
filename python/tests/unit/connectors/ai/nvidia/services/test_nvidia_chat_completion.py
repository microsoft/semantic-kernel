# Copyright (c) Microsoft. All rights reserved.

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import BaseModel

from semantic_kernel.connectors.ai.nvidia import NvidiaChatCompletion
from semantic_kernel.connectors.ai.nvidia.prompt_execution_settings.nvidia_prompt_execution_settings import (
    NvidiaChatPromptExecutionSettings,
)
from semantic_kernel.contents import ChatHistory
from semantic_kernel.contents.author_role import AuthorRole


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    with patch("semantic_kernel.connectors.ai.nvidia.services.nvidia_chat_completion.AsyncOpenAI") as mock_client:
        mock_client.return_value = AsyncMock()
        yield mock_client.return_value


@pytest.fixture
def nvidia_chat_completion(mock_openai_client):
    """Create a NvidiaChatCompletion instance with mocked client."""
    return NvidiaChatCompletion(
        ai_model_id="meta/llama-3.1-8b-instruct",
        api_key="test-api-key",
    )


class TestNvidiaChatCompletion:
    """Test cases for NvidiaChatCompletion."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        with patch("semantic_kernel.connectors.ai.nvidia.services.nvidia_chat_completion.AsyncOpenAI"):
            service = NvidiaChatCompletion(api_key="test-key")
            assert service.ai_model_id == "meta/llama-3.1-8b-instruct"

    def test_get_prompt_execution_settings_class(self, nvidia_chat_completion):
        """Test getting the prompt execution settings class."""
        from semantic_kernel.connectors.ai.nvidia.prompt_execution_settings.nvidia_prompt_execution_settings import NvidiaChatPromptExecutionSettings
        assert nvidia_chat_completion.get_prompt_execution_settings_class() == NvidiaChatPromptExecutionSettings

    @pytest.mark.asyncio
    async def test_get_chat_message_contents(self, nvidia_chat_completion, mock_openai_client):
        """Test basic chat completion."""
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

        # Test
        chat_history = ChatHistory()
        chat_history.add_message(AuthorRole.USER, "Hello")
        settings = NvidiaChatPromptExecutionSettings()
        
        result = await nvidia_chat_completion.get_chat_message_contents(chat_history, settings)
        
        assert len(result) == 1
        assert result[0].content == "Hello!"

    @pytest.mark.asyncio
    async def test_structured_output_with_pydantic_model(self, nvidia_chat_completion, mock_openai_client):
        """Test structured output with Pydantic model."""
        # Define test model
        class TestModel(BaseModel):
            name: str
            value: int

        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(role="assistant", content='{"name": "test", "value": 42}'),
                finish_reason="stop",
            )
        ]
        mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        mock_openai_client.chat.completions.create.return_value = mock_response

        # Test
        chat_history = ChatHistory()
        chat_history.add_message(AuthorRole.USER, "Give me structured data")
        settings = NvidiaChatPromptExecutionSettings()
        settings.response_format = TestModel
        
        result = await nvidia_chat_completion.get_chat_message_contents(chat_history, settings)
        
        # Verify nvext was passed
        call_args = mock_openai_client.chat.completions.create.call_args[1]
        assert "extra_body" in call_args
        assert "nvext" in call_args["extra_body"]
        assert "guided_json" in call_args["extra_body"]["nvext"]

    @pytest.mark.asyncio
    async def test_error_handling(self, nvidia_chat_completion, mock_openai_client):
        """Test error handling."""
        mock_openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        chat_history = ChatHistory()
        chat_history.add_message(AuthorRole.USER, "Hello")
        settings = NvidiaChatPromptExecutionSettings()
        
        from semantic_kernel.exceptions import ServiceResponseException
        with pytest.raises(ServiceResponseException):
            await nvidia_chat_completion.get_chat_message_contents(chat_history, settings) 