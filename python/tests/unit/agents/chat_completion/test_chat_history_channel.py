# Copyright (c) Microsoft. All rights reserved.

from collections.abc import AsyncIterable
from unittest.mock import AsyncMock

from semantic_kernel.agents.channels.chat_history_channel import ChatHistoryChannel
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.file_reference_content import FileReferenceContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.streaming_file_reference_content import StreamingFileReferenceContent
from semantic_kernel.contents.utils.author_role import AuthorRole


class MockChatHistoryHandler:
    """Mock agent to test chat history handling"""

    async def invoke(self, history: list[ChatMessageContent]) -> AsyncIterable[ChatMessageContent]:
        for message in history:
            yield ChatMessageContent(role=AuthorRole.SYSTEM, content=f"Processed: {message.content}")

    async def invoke_stream(self, history: list[ChatMessageContent]) -> AsyncIterable[ChatMessageContent]:
        for message in history:
            yield ChatMessageContent(role=AuthorRole.SYSTEM, content=f"Processed: {message.content}")

    async def reduce_history(self, history: list[ChatMessageContent]) -> list[ChatMessageContent]:
        return history


class MockNonChatHistoryHandler:
    """Mock agent to test incorrect instance handling."""

    id: str = "mock_non_chat_history_handler"


class AsyncIterableMock:
    def __init__(self, async_gen):
        self.async_gen = async_gen

    def __aiter__(self):
        return self.async_gen()


async def test_invoke():
    channel = ChatHistoryChannel()
    agent = AsyncMock(spec=MockChatHistoryHandler)

    async def mock_invoke(history: list[ChatMessageContent]):
        for message in history:
            yield ChatMessageContent(role=AuthorRole.SYSTEM, content=f"Processed: {message.content}")

    agent.invoke.return_value = AsyncIterableMock(
        lambda: mock_invoke([ChatMessageContent(role=AuthorRole.USER, content="Initial message")])
    )

    initial_message = ChatMessageContent(role=AuthorRole.USER, content="Initial message")
    channel.messages.append(initial_message)

    received_messages = []
    async for is_visible, message in channel.invoke(agent):
        received_messages.append(message)
        assert is_visible

    assert len(received_messages) == 1
    assert "Processed: Initial message" in received_messages[0].content


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


async def test_invoke_leftover_in_queue():
    channel = ChatHistoryChannel()
    agent = AsyncMock(spec=MockChatHistoryHandler)

    async def mock_invoke(history: list[ChatMessageContent]):
        for message in history:
            yield ChatMessageContent(role=AuthorRole.SYSTEM, content=f"Processed: {message.content}")
        yield ChatMessageContent(
            role=AuthorRole.SYSTEM, content="Final message", items=[FunctionResultContent(id="test_id", result="test")]
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

    initial_message = ChatMessageContent(role=AuthorRole.USER, content="Initial message")
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


async def test_receive_skips_file_references():
    channel = ChatHistoryChannel()

    file_ref_item = FileReferenceContent()
    streaming_file_ref_item = StreamingFileReferenceContent()
    normal_item_1 = FunctionResultContent(id="test_id", result="normal content 1")
    normal_item_2 = FunctionResultContent(id="test_id_2", result="normal content 2")

    msg_with_file_only = ChatMessageContent(
        role=AuthorRole.USER,
        content="Normal message set as TextContent",
        items=[file_ref_item],
    )

    msg_with_mixed = ChatMessageContent(
        role=AuthorRole.USER,
        content="Mixed content message",
        items=[streaming_file_ref_item, normal_item_1],
    )

    msg_with_normal = ChatMessageContent(
        role=AuthorRole.USER,
        content="Normal message",
        items=[normal_item_2],
    )

    history = [msg_with_file_only, msg_with_mixed, msg_with_normal]
    await channel.receive(history)

    assert len(channel.messages) == 3

    assert channel.messages[0].content == "Normal message set as TextContent"
    assert len(channel.messages[0].items) == 1

    assert channel.messages[1].content == "Mixed content message"
    assert len(channel.messages[0].items) == 1
    assert channel.messages[1].items[0].result == "normal content 1"

    assert channel.messages[2].content == "Normal message"
    assert len(channel.messages[2].items) == 2
    assert channel.messages[2].items[0].result == "normal content 2"
    assert channel.messages[2].items[1].text == "Normal message"
