# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch

import pytest

from semantic_kernel.connectors.ai.google.google_ai.google_ai_prompt_execution_settings import (
    GoogleAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.google.google_ai.services.google_ai_chat_completion import GoogleAIChatCompletion
from semantic_kernel.const import USER_AGENT
from semantic_kernel.contents.chat_history import ChatHistory


@pytest.mark.asyncio
async def test_google_ai_chat_completion_user_agent(google_ai_unit_test_env):
    """Test that GoogleAIChatCompletion sends the User-Agent header."""
    chat_history = ChatHistory()
    chat_history.add_user_message("hi")

    with patch(
        "semantic_kernel.connectors.ai.google.google_ai.services.google_ai_chat_completion.Client"
    ) as mock_client:
        mock_instance = mock_client.return_value.__enter__.return_value
        mock_instance.aio.models.generate_content = AsyncMock()

        service = GoogleAIChatCompletion(gemini_model_id="gemini-3-flash-preview", api_key="AIza-test-key")

        await service.get_chat_message_contents(
            chat_history=chat_history, settings=GoogleAIChatPromptExecutionSettings()
        )

        _, kwargs = mock_client.call_args
        assert "http_options" in kwargs
        assert kwargs["http_options"] is not None
        assert "headers" in kwargs["http_options"]
        assert USER_AGENT in kwargs["http_options"]["headers"]
        assert "semantic-kernel-python" in kwargs["http_options"]["headers"][USER_AGENT]


@pytest.mark.asyncio
async def test_google_ai_chat_completion_no_telemetry(google_ai_unit_test_env):
    """Test that GoogleAIChatCompletion does not send the User-Agent header when telemetry is disabled."""
    chat_history = ChatHistory()
    chat_history.add_user_message("hi")

    with (
        patch("semantic_kernel.connectors.ai.google.google_ai.services.google_ai_base.APP_INFO", None),
        patch(
            "semantic_kernel.connectors.ai.google.google_ai.services.google_ai_chat_completion.Client"
        ) as mock_client,
    ):
        mock_instance = mock_client.return_value.__enter__.return_value
        mock_instance.aio.models.generate_content = AsyncMock()

        service = GoogleAIChatCompletion(gemini_model_id="gemini-3-flash-preview", api_key="AIza-test-key")

        await service.get_chat_message_contents(
            chat_history=chat_history, settings=GoogleAIChatPromptExecutionSettings()
        )

        _, kwargs = mock_client.call_args
        assert "http_options" in kwargs
        assert kwargs["http_options"] is None
