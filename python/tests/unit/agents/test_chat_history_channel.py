# Copyright (c) Microsoft. All rights reserved.

from collections.abc import AsyncIterable
from unittest.mock import AsyncMock

import pytest

<<<<<<< main
from semantic_kernel.agents.chat_history_channel import (
    ChatHistoryAgentProtocol,
    ChatHistoryChannel,
)
=======
from semantic_kernel.agents.channels.chat_history_channel import ChatHistoryAgentProtocol, ChatHistoryChannel
>>>>>>> upstream/main
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions import ServiceInvalidTypeError


class MockChatHistoryHandler:
    """Mock agent to test chat history handling"""

    async def invoke(
        self, history: list[ChatMessageContent]
    ) -> AsyncIterable[ChatMessageContent]:
        for message in history:
            yield ChatMessageContent(
                role=AuthorRole.SYSTEM, content=f"Processed: {message.content}"
            )

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
    async def invoke_stream(self, history: list[ChatMessageContent]) -> AsyncIterable[ChatMessageContent]:
        for message in history:
            yield ChatMessageContent(role=AuthorRole.SYSTEM, content=f"Processed: {message.content}")

<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head

class MockNonChatHistoryHandler:
    """Mock agent to test incorrect instance handling."""

    id: str = "mock_non_chat_history_handler"


ChatHistoryAgentProtocol.register(MockChatHistoryHandler)


class AsyncIterableMock:
    def __init__(self, async_gen):
        self.async_gen = async_gen

    def __aiter__(self):
        return self.async_gen()


@pytest.mark.asyncio
async def test_invoke():
    channel = ChatHistoryChannel()
    agent = AsyncMock(spec=MockChatHistoryHandler)

    async def mock_invoke(history: list[ChatMessageContent]):
        for message in history:
            yield ChatMessageContent(
                role=AuthorRole.SYSTEM, content=f"Processed: {message.content}"
            )

    agent.invoke.return_value = AsyncIterableMock(
        lambda: mock_invoke(
            [ChatMessageContent(role=AuthorRole.USER, content="Initial message")]
        )
    )

    initial_message = ChatMessageContent(
        role=AuthorRole.USER, content="Initial message"
    )
    channel.messages.append(initial_message)

    received_messages = []
    async for is_visible, message in channel.invoke(agent):
        received_messages.append(message)
        assert is_visible

    assert len(received_messages) == 1
    assert "Processed: Initial message" in received_messages[0].content


@pytest.mark.asyncio
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
async def test_invoke_stream():
    channel = ChatHistoryChannel()
    agent = AsyncMock(spec=MockChatHistoryHandler)

    async def mock_invoke(history: list[ChatMessageContent]):
        for message in history:
            msg = ChatMessageContent(role=AuthorRole.SYSTEM, content=f"Processed: {message.content}")
            yield msg
            channel.add_message(msg)

    agent.invoke_stream.return_value = AsyncIterableMock(
        lambda: mock_invoke([ChatMessageContent(role=AuthorRole.USER, content="Initial message")])
    )

    initial_message = ChatMessageContent(role=AuthorRole.USER, content="Initial message")
    channel.messages.append(initial_message)

    received_messages = []
    async for message in channel.invoke_stream(agent, received_messages):
        assert message is not None

    assert len(received_messages) == 1
    assert "Processed: Initial message" in received_messages[0].content


@pytest.mark.asyncio
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
async def test_invoke_leftover_in_queue():
    channel = ChatHistoryChannel()
    agent = AsyncMock(spec=MockChatHistoryHandler)

    async def mock_invoke(history: list[ChatMessageContent]):
        for message in history:
            yield ChatMessageContent(
                role=AuthorRole.SYSTEM, content=f"Processed: {message.content}"
            )
        yield ChatMessageContent(
            role=AuthorRole.SYSTEM,
            content="Final message",
            items=[FunctionResultContent(id="test_id", result="test")],
        )

    agent.invoke.return_value = AsyncIterableMock(
        lambda: mock_invoke([
            ChatMessageContent(
                role=AuthorRole.USER,
                content="Initial message",
                items=[FunctionResultContent(id="test_id", result="test")],
            )
        ])
    )

    initial_message = ChatMessageContent(
        role=AuthorRole.USER, content="Initial message"
    )
    channel.messages.append(initial_message)

    received_messages = []
    async for is_visible, message in channel.invoke(agent):
        received_messages.append(message)
        assert is_visible
        if len(received_messages) >= 3:
            break

    assert len(received_messages) == 3
    assert "Processed: Initial message" in received_messages[0].content
    assert "Final message" in received_messages[2].content
    assert received_messages[2].items[0].id == "test_id"


@pytest.mark.asyncio
async def test_invoke_incorrect_instance_throws():
    channel = ChatHistoryChannel()
    agent = MockNonChatHistoryHandler()

    with pytest.raises(ServiceInvalidTypeError):
        async for _ in channel.invoke(agent):
            pass


@pytest.mark.asyncio
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
async def test_invoke_stream_incorrect_instance_throws():
    channel = ChatHistoryChannel()
    agent = MockNonChatHistoryHandler()

    with pytest.raises(ServiceInvalidTypeError):
        async for _ in channel.invoke_stream(agent, []):
            pass


@pytest.mark.asyncio
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
async def test_receive():
    channel = ChatHistoryChannel()
    history = [
        ChatMessageContent(role=AuthorRole.SYSTEM, content="test message 1"),
        ChatMessageContent(role=AuthorRole.USER, content="test message 2"),
    ]

    await channel.receive(history)

    assert len(channel.messages) == 2
    assert channel.messages[0].content == "test message 1"
    assert channel.messages[0].role == AuthorRole.SYSTEM
    assert channel.messages[1].content == "test message 2"
    assert channel.messages[1].role == AuthorRole.USER


@pytest.mark.asyncio
async def test_get_history():
    channel = ChatHistoryChannel()
    history = [
        ChatMessageContent(role=AuthorRole.SYSTEM, content="test message 1"),
        ChatMessageContent(role=AuthorRole.USER, content="test message 2"),
    ]
    channel.messages.extend(history)

    messages = [message async for message in channel.get_history()]

    assert len(messages) == 2
    assert messages[0].content == "test message 2"
    assert messages[0].role == AuthorRole.USER
    assert messages[1].content == "test message 1"
    assert messages[1].role == AuthorRole.SYSTEM


@pytest.mark.asyncio
async def test_reset_history():
    channel = ChatHistoryChannel()
    history = [
        ChatMessageContent(role=AuthorRole.SYSTEM, content="test message 1"),
        ChatMessageContent(role=AuthorRole.USER, content="test message 2"),
    ]
    channel.messages.extend(history)

    messages = [message async for message in channel.get_history()]

    assert len(messages) == 2
    assert messages[0].content == "test message 2"
    assert messages[0].role == AuthorRole.USER
    assert messages[1].content == "test message 1"
    assert messages[1].role == AuthorRole.SYSTEM

    await channel.reset()

    assert len(channel.messages) == 0
