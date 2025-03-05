# Copyright (c) Microsoft. All rights reserved.


from unittest.mock import AsyncMock, patch

from openai import AsyncOpenAI
from openai.types.beta.assistant import Assistant

from semantic_kernel.agents.open_ai.open_ai_assistant_agent import OpenAIAssistantAgent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole


@patch("semantic_kernel.utils.telemetry.agent_diagnostics.decorators.tracer")
async def test_open_ai_assistant_agent_invoke(mock_tracer, chat_history, openai_unit_test_env):
    # Arrange
    client = AsyncMock(spec=AsyncOpenAI)
    definition = AsyncMock(spec=Assistant)
    definition.name = "agentName"
    definition.description = "agentDescription"
    definition.id = "agentId"
    definition.instructions = "agentInstructions"
    definition.tools = []
    definition.model = "agentModel"
    definition.temperature = 1.0
    definition.top_p = 1.0
    definition.metadata = {}
    open_ai_assistant_agent = OpenAIAssistantAgent(client=client, definition=definition)

    async def fake_invoke(*args, **kwargs):
        yield True, ChatMessageContent(role=AuthorRole.ASSISTANT, content="content")

    # Act
    with patch(
        "semantic_kernel.agents.open_ai.assistant_thread_actions.AssistantThreadActions.invoke",
        side_effect=fake_invoke,
    ):
        async for item in open_ai_assistant_agent.invoke("thread_id"):
            pass
    # Assert
    mock_tracer.start_as_current_span.assert_called_once_with(f"invoke_agent {open_ai_assistant_agent.name}")


@patch("semantic_kernel.utils.telemetry.agent_diagnostics.decorators.tracer")
async def test_open_ai_assistant_agent_invoke_stream(mock_tracer, chat_history, openai_unit_test_env):
    # Arrange
    client = AsyncMock(spec=AsyncOpenAI)
    definition = AsyncMock(spec=Assistant)
    definition.name = "agentName"
    definition.description = "agentDescription"
    definition.id = "agentId"
    definition.instructions = "agentInstructions"
    definition.tools = []
    definition.model = "agentModel"
    definition.temperature = 1.0
    definition.top_p = 1.0
    definition.metadata = {}
    open_ai_assistant_agent = OpenAIAssistantAgent(client=client, definition=definition)

    async def fake_invoke(*args, **kwargs):
        yield True, ChatMessageContent(role=AuthorRole.ASSISTANT, content="content")

    # Act
    with patch(
        "semantic_kernel.agents.open_ai.assistant_thread_actions.AssistantThreadActions.invoke_stream",
        side_effect=fake_invoke,
    ):
        async for item in open_ai_assistant_agent.invoke_stream("thread_id"):
            pass
    # Assert
    mock_tracer.start_as_current_span.assert_called_once_with(f"invoke_agent {open_ai_assistant_agent.name}")
