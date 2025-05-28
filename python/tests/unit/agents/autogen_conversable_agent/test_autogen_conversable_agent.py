# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock

import pytest
from autogen import ConversableAgent

from semantic_kernel.agents.autogen.autogen_conversable_agent import (
    AutoGenConversableAgent,
    AutoGenConversableAgentThread,
)
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentInvokeException


@pytest.fixture
def mock_conversable_agent():
    agent = MagicMock(spec=ConversableAgent)
    agent.name = "MockName"
    agent.description = "MockDescription"
    agent.system_message = "MockSystemMessage"
    return agent


async def test_autogen_conversable_agent_initialization(mock_conversable_agent):
    agent = AutoGenConversableAgent(mock_conversable_agent, id="mock_id")
    assert agent.name == "MockName"
    assert agent.description == "MockDescription"
    assert agent.instructions == "MockSystemMessage"
    assert agent.conversable_agent == mock_conversable_agent


async def test_autogen_conversable_agent_get_response(mock_conversable_agent):
    mock_conversable_agent.a_generate_reply = AsyncMock(return_value="Mocked assistant response")
    agent = AutoGenConversableAgent(mock_conversable_agent)
    thread: AutoGenConversableAgentThread = None

    response = await agent.get_response("Hello", thread=thread)
    assert response.message.role == AuthorRole.ASSISTANT
    assert response.message.content == "Mocked assistant response"
    assert response.thread is not None


async def test_autogen_conversable_agent_get_response_exception(mock_conversable_agent):
    mock_conversable_agent.a_generate_reply = AsyncMock(return_value=None)
    agent = AutoGenConversableAgent(mock_conversable_agent)

    with pytest.raises(AgentInvokeException):
        await agent.get_response("Hello")


async def test_autogen_conversable_agent_invoke_with_recipient(mock_conversable_agent):
    mock_conversable_agent.a_initiate_chat = AsyncMock()
    mock_conversable_agent.a_initiate_chat.return_value = MagicMock(
        chat_history=[
            {"role": "user", "content": "Hello from user!"},
            {"role": "assistant", "content": "Hello from assistant!"},
        ]
    )
    agent = AutoGenConversableAgent(mock_conversable_agent)
    recipient_agent = MagicMock(spec=AutoGenConversableAgent)
    recipient_agent.conversable_agent = MagicMock(spec=ConversableAgent)

    messages = []
    async for response in agent.invoke(recipient=recipient_agent, messages="Test message", arg1="arg1"):
        messages.append(response)

    mock_conversable_agent.a_initiate_chat.assert_awaited_once()
    assert len(messages) == 2
    assert messages[0].message.role == AuthorRole.USER
    assert messages[0].message.content == "Hello from user!"
    assert messages[1].message.role == AuthorRole.ASSISTANT
    assert messages[1].message.content == "Hello from assistant!"


async def test_autogen_conversable_agent_invoke_without_recipient_string_reply(mock_conversable_agent):
    mock_conversable_agent.a_generate_reply = AsyncMock(return_value="Mocked assistant response")
    agent = AutoGenConversableAgent(mock_conversable_agent)

    responses = []
    async for response in agent.invoke(messages="Hello"):
        responses.append(response)

    mock_conversable_agent.a_generate_reply.assert_awaited_once()
    assert len(responses) == 1
    assert responses[0].message.role == AuthorRole.ASSISTANT
    assert responses[0].message.content == "Mocked assistant response"


async def test_autogen_conversable_agent_invoke_without_recipient_dict_reply(mock_conversable_agent):
    mock_conversable_agent.a_generate_reply = AsyncMock(
        return_value={
            "content": "Mocked assistant response",
            "role": "assistant",
            "name": "AssistantName",
        }
    )
    agent = AutoGenConversableAgent(mock_conversable_agent)

    responses = []
    async for response in agent.invoke(messages="Hello"):
        responses.append(response)

    mock_conversable_agent.a_generate_reply.assert_awaited_once()
    assert len(responses) == 1
    assert responses[0].message.role == AuthorRole.ASSISTANT
    assert responses[0].message.content == "Mocked assistant response"
    assert responses[0].message.name == "AssistantName"


async def test_autogen_conversable_agent_invoke_without_recipient_unexpected_type(mock_conversable_agent):
    mock_conversable_agent.a_generate_reply = AsyncMock(return_value=12345)
    agent = AutoGenConversableAgent(mock_conversable_agent)

    with pytest.raises(AgentInvokeException):
        async for _ in agent.invoke(messages="Hello"):
            pass


async def test_autogen_conversable_agent_invoke_with_invalid_recipient_type(mock_conversable_agent):
    mock_conversable_agent.a_generate_reply = AsyncMock(return_value=12345)
    agent = AutoGenConversableAgent(mock_conversable_agent)

    recipient = MagicMock()

    with pytest.raises(AgentInvokeException):
        async for _ in agent.invoke(recipient=recipient, messages="Hello"):
            pass
