# Copyright (c) Microsoft. All rights reserved.


from unittest.mock import patch

import pytest

from semantic_kernel.agents.open_ai.open_ai_assistant_agent import OpenAIAssistantAgent
from semantic_kernel.exceptions.agent_exceptions import AgentInitializationException


@patch("semantic_kernel.utils.telemetry.agent_diagnostics.decorators.tracer")
async def test_open_ai_assistant_agent_invoke(mock_tracer, chat_history, openai_unit_test_env):
    # Arrange
    open_ai_assistant_agent = OpenAIAssistantAgent()
    # Act
    with pytest.raises(AgentInitializationException):
        async for _ in open_ai_assistant_agent.invoke(chat_history):
            pass
    # Assert
    mock_tracer.start_as_current_span.assert_called_once_with(open_ai_assistant_agent.name)


@patch("semantic_kernel.utils.telemetry.agent_diagnostics.decorators.tracer")
async def test_open_ai_assistant_agent_invoke_stream(mock_tracer, chat_history, openai_unit_test_env):
    # Arrange
    open_ai_assistant_agent = OpenAIAssistantAgent()
    # Act
    with pytest.raises(AgentInitializationException):
        async for _ in open_ai_assistant_agent.invoke_stream(chat_history):
            pass
    # Assert
    mock_tracer.start_as_current_span.assert_called_once_with(open_ai_assistant_agent.name)
