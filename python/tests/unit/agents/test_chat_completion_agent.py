# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, create_autospec, patch

import pytest
from pydantic import ValidationError

from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.agents.channels.chat_history_channel import ChatHistoryChannel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions import KernelServiceNotFoundError
from semantic_kernel.kernel import Kernel


@pytest.fixture
def mock_streaming_chat_completion_response() -> AsyncMock:
    """A fixture that returns a mock response for a streaming chat completion response."""

    async def mock_response(chat_history, settings, kernel):
        content1 = ChatMessageContent(role=AuthorRole.SYSTEM, content="Processed Message 1")
        content2 = ChatMessageContent(role=AuthorRole.TOOL, content="Processed Message 2")
        chat_history.messages.append(content1)
        chat_history.messages.append(content2)
        yield [content1]
        yield [content2]

    return mock_response


async def test_initialization():
    agent = ChatCompletionAgent(
        service_id="test_service",
        name="TestAgent",
        id="test_id",
        description="Test Description",
        instructions="Test Instructions",
    )

    assert agent.service_id == "test_service"
    assert agent.name == "TestAgent"
    assert agent.id == "test_id"
    assert agent.description == "Test Description"
    assert agent.instructions == "Test Instructions"


async def test_initialization_invalid_name_throws():
    with pytest.raises(ValidationError):
        _ = ChatCompletionAgent(
            service_id="test_service",
            name="Test Agent",
            id="test_id",
            description="Test Description",
            instructions="Test Instructions",
        )


async def test_initialization_no_service_id():
    agent = ChatCompletionAgent(
        name="TestAgent",
        id="test_id",
        description="Test Description",
        instructions="Test Instructions",
    )

    assert agent.service_id == "default"
    assert agent.kernel is not None
    assert agent.name == "TestAgent"
    assert agent.id == "test_id"
    assert agent.description == "Test Description"
    assert agent.instructions == "Test Instructions"


async def test_initialization_with_kernel(kernel: Kernel):
    agent = ChatCompletionAgent(
        kernel=kernel,
        name="TestAgent",
        id="test_id",
        description="Test Description",
        instructions="Test Instructions",
    )

    assert agent.service_id == "default"
    assert kernel == agent.kernel
    assert agent.name == "TestAgent"
    assert agent.id == "test_id"
    assert agent.description == "Test Description"
    assert agent.instructions == "Test Instructions"


async def test_invoke():
    kernel = create_autospec(Kernel)
    kernel.get_service.return_value = create_autospec(ChatCompletionClientBase)
    kernel.get_service.return_value.get_chat_message_contents = AsyncMock(
        return_value=[ChatMessageContent(role=AuthorRole.SYSTEM, content="Processed Message")]
    )
    agent = ChatCompletionAgent(
        kernel=kernel, service_id="test_service", name="TestAgent", instructions="Test Instructions"
    )

    history = ChatHistory(messages=[ChatMessageContent(role=AuthorRole.USER, content="Initial Message")])

    messages = [message async for message in agent.invoke(history)]

    assert len(messages) == 1
    assert messages[0].content == "Processed Message"


async def test_invoke_tool_call_added():
    kernel = create_autospec(Kernel)
    chat_completion_service = create_autospec(ChatCompletionClientBase)
    kernel.get_service.return_value = chat_completion_service
    agent = ChatCompletionAgent(kernel=kernel, service_id="test_service", name="TestAgent")

    history = ChatHistory(messages=[ChatMessageContent(role=AuthorRole.USER, content="Initial Message")])

    async def mock_get_chat_message_contents(chat_history, settings, kernel):
        new_messages = [
            ChatMessageContent(role=AuthorRole.ASSISTANT, content="Processed Message 1"),
            ChatMessageContent(role=AuthorRole.TOOL, content="Processed Message 2"),
        ]
        chat_history.messages.extend(new_messages)
        return new_messages

    chat_completion_service.get_chat_message_contents = AsyncMock(side_effect=mock_get_chat_message_contents)

    messages = [message async for message in agent.invoke(history)]

    assert len(messages) == 2
    assert messages[0].content == "Processed Message 1"
    assert messages[1].content == "Processed Message 2"

    assert len(history.messages) == 3
    assert history.messages[1].content == "Processed Message 1"
    assert history.messages[2].content == "Processed Message 2"
    assert history.messages[1].name == "TestAgent"
    assert history.messages[2].name == "TestAgent"


async def test_invoke_no_service_throws():
    kernel = create_autospec(Kernel)
    kernel.get_service.return_value = None
    agent = ChatCompletionAgent(kernel=kernel, service_id="test_service", name="TestAgent")

    history = ChatHistory(messages=[ChatMessageContent(role=AuthorRole.USER, content="Initial Message")])

    with pytest.raises(KernelServiceNotFoundError):
        async for _ in agent.invoke(history):
            pass


async def test_invoke_stream():
    kernel = create_autospec(Kernel)
    kernel.get_service.return_value = create_autospec(ChatCompletionClientBase)

    agent = ChatCompletionAgent(kernel=kernel, service_id="test_service", name="TestAgent")

    history = ChatHistory(messages=[ChatMessageContent(role=AuthorRole.USER, content="Initial Message")])

    with patch(
        "semantic_kernel.connectors.ai.chat_completion_client_base.ChatCompletionClientBase.get_streaming_chat_message_contents",
        return_value=AsyncMock(),
    ) as mock:
        mock.return_value.__aiter__.return_value = [
            [ChatMessageContent(role=AuthorRole.USER, content="Initial Message")]
        ]

        async for message in agent.invoke_stream(history):
            assert message.role == AuthorRole.USER
            assert message.content == "Initial Message"


async def test_invoke_stream_tool_call_added(mock_streaming_chat_completion_response):
    kernel = create_autospec(Kernel)
    chat_completion_service = create_autospec(ChatCompletionClientBase)
    kernel.get_service.return_value = chat_completion_service
    agent = ChatCompletionAgent(kernel=kernel, service_id="test_service", name="TestAgent")

    history = ChatHistory(messages=[ChatMessageContent(role=AuthorRole.USER, content="Initial Message")])

    chat_completion_service.get_streaming_chat_message_contents = mock_streaming_chat_completion_response

    async for message in agent.invoke_stream(history):
        print(f"Message role: {message.role}, content: {message.content}")
        assert message.role in [AuthorRole.SYSTEM, AuthorRole.TOOL]
        assert message.content in ["Processed Message 1", "Processed Message 2"]

    assert len(history.messages) == 3


async def test_invoke_stream_no_service_throws():
    kernel = create_autospec(Kernel)
    kernel.get_service.return_value = None
    agent = ChatCompletionAgent(kernel=kernel, service_id="test_service", name="TestAgent")

    history = ChatHistory(messages=[ChatMessageContent(role=AuthorRole.USER, content="Initial Message")])

    with pytest.raises(KernelServiceNotFoundError):
        async for _ in agent.invoke_stream(history):
            pass


def test_get_channel_keys():
    agent = ChatCompletionAgent()
    keys = agent.get_channel_keys()

    for key in keys:
        assert isinstance(key, str)


async def test_create_channel():
    agent = ChatCompletionAgent()
    channel = await agent.create_channel()

    assert isinstance(channel, ChatHistoryChannel)
