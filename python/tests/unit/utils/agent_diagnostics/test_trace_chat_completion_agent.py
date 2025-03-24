# Copyright (c) Microsoft. All rights reserved.


from unittest.mock import patch

import pytest

from semantic_kernel.agents.chat_completion.chat_completion_agent import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.exceptions.kernel_exceptions import KernelServiceNotFoundError


@patch("semantic_kernel.utils.telemetry.agent_diagnostics.decorators.tracer")
async def test_chat_completion_agent_invoke(mock_tracer, chat_history):
    # Arrange
    chat_completion_agent = ChatCompletionAgent()
    thread = ChatHistoryAgentThread(chat_history=chat_history)
    # Act
    with pytest.raises(KernelServiceNotFoundError):
        async for _ in chat_completion_agent.invoke(messages="test", thread=thread):
            pass
    # Assert
    mock_tracer.start_as_current_span.assert_called_once_with(f"invoke_agent {chat_completion_agent.name}")


@patch("semantic_kernel.utils.telemetry.agent_diagnostics.decorators.tracer")
async def test_chat_completion_agent_invoke_stream(mock_tracer, chat_history):
    # Arrange
    chat_completion_agent = ChatCompletionAgent()
    thread = ChatHistoryAgentThread(chat_history=chat_history)
    # Act
    with pytest.raises(KernelServiceNotFoundError):
        async for _ in chat_completion_agent.invoke_stream(messages="test", thread=thread):
            pass
    # Assert
    mock_tracer.start_as_current_span.assert_called_once_with(f"invoke_agent {chat_completion_agent.name}")
