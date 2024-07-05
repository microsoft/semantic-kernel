# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, create_autospec, patch

import pytest

from semantic_kernel.agents.chat_completion_agent import ChatCompletionAgent
from semantic_kernel.agents.chat_history_channel import ChatHistoryChannel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions import KernelServiceNotFoundError
from semantic_kernel.kernel import Kernel


@pytest.mark.asyncio
async def test_initialization():
    agent = ChatCompletionAgent(
        service_id="test_service",
        name="Test Agent",
        id="test_id",
        description="Test Description",
        instructions="Test Instructions",
    )

    assert agent.service_id == "test_service"
    assert agent.name == "Test Agent"
    assert agent.id == "test_id"
    assert agent.description == "Test Description"
    assert agent.instructions == "Test Instructions"


@pytest.mark.asyncio
async def test_invoke():
    agent = ChatCompletionAgent(service_id="test_service", name="Test Agent", instructions="Test Instructions")

    kernel = create_autospec(Kernel)
    kernel.get_service.return_value = create_autospec(ChatCompletionClientBase)
    kernel.get_service.return_value.get_chat_message_contents = AsyncMock(
        return_value=[ChatMessageContent(role=AuthorRole.SYSTEM, content="Processed Message")]
    )

    history = ChatHistory(messages=[ChatMessageContent(role=AuthorRole.USER, content="Initial Message")])

    messages = [message async for message in agent.invoke(kernel, history)]

    assert len(messages) == 1
    assert messages[0].content == "Processed Message"


@pytest.mark.asyncio
async def test_invoke_tool_call_added():
    agent = ChatCompletionAgent(service_id="test_service", name="Test Agent")

    kernel = create_autospec(Kernel)
    chat_completion_service = create_autospec(ChatCompletionClientBase)
    kernel.get_service.return_value = chat_completion_service

    history = ChatHistory(messages=[ChatMessageContent(role=AuthorRole.USER, content="Initial Message")])

    async def mock_get_chat_message_contents(chat_history, settings, kernel, arguments):
        new_messages = [
            ChatMessageContent(role=AuthorRole.SYSTEM, content="Processed Message 1"),
            ChatMessageContent(role=AuthorRole.TOOL, content="Processed Message 2"),
        ]
        chat_history.messages.extend(new_messages)
        return new_messages

    chat_completion_service.get_chat_message_contents = AsyncMock(side_effect=mock_get_chat_message_contents)

    messages = [message async for message in agent.invoke(kernel, history)]

    assert len(messages) == 2
    assert messages[0].content == "Processed Message 1"
    assert messages[1].content == "Processed Message 2"

    assert len(history.messages) == 3
    assert history.messages[1].content == "Processed Message 1"
    assert history.messages[2].content == "Processed Message 2"
    assert history.messages[1].name == "Test Agent"
    assert history.messages[2].name == "Test Agent"


@pytest.mark.asyncio
async def test_invoke_no_service_throws():
    agent = ChatCompletionAgent(service_id="test_service", name="Test Agent")

    kernel = create_autospec(Kernel)
    kernel.get_service.return_value = None

    history = ChatHistory(messages=[ChatMessageContent(role=AuthorRole.USER, content="Initial Message")])

    with pytest.raises(KernelServiceNotFoundError):
        async for _ in agent.invoke(kernel, history):
            pass


@pytest.mark.asyncio
async def test_invoke_streaming():
    agent = ChatCompletionAgent(service_id="test_service", name="Test Agent")

    kernel = create_autospec(Kernel)

    history = ChatHistory(messages=[ChatMessageContent(role=AuthorRole.USER, content="Initial Message")])

    with patch(
        "semantic_kernel.connectors.ai.chat_completion_client_base.ChatCompletionClientBase.get_streaming_chat_message_contents",
        return_value=AsyncMock(),
    ) as mock:
        mock.return_value.__aiter__.return_value = [ChatMessageContent(role=AuthorRole.USER, content="Initial Message")]

        async for message in agent.invoke_streaming(kernel, history):
            assert message.role == AuthorRole.USER
            assert message.content == "Initial Message"


@pytest.mark.asyncio
async def test_invoke_streaming_no_service_throws():
    agent = ChatCompletionAgent(service_id="test_service", name="Test Agent")

    kernel = create_autospec(Kernel)
    kernel.get_service.return_value = None

    history = ChatHistory(messages=[ChatMessageContent(role=AuthorRole.USER, content="Initial Message")])

    with pytest.raises(KernelServiceNotFoundError):
        async for _ in agent.invoke_streaming(kernel, history):
            pass


def test_get_channel_keys():
    agent = ChatCompletionAgent()
    keys = agent.get_channel_keys()

    assert keys == [ChatHistoryChannel.__name__]


def test_create_channel():
    agent = ChatCompletionAgent()
    channel = agent.create_channel()

    assert isinstance(channel, ChatHistoryChannel)
