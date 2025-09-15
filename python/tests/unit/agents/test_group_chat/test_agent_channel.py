# Copyright (c) Microsoft. All rights reserved.

from collections.abc import AsyncIterable
from unittest.mock import AsyncMock

from semantic_kernel.agents import Agent
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole


class MockAgentChannel(AgentChannel):
    async def receive(self, history: list[ChatMessageContent]) -> None:
        pass

    async def invoke(self, agent: "Agent") -> AsyncIterable[ChatMessageContent]:
        yield ChatMessageContent(role=AuthorRole.SYSTEM, content="test message")

    async def get_history(self) -> AsyncIterable[ChatMessageContent]:
        yield ChatMessageContent(role=AuthorRole.SYSTEM, content="test history message")


async def test_receive():
    mock_channel = AsyncMock(spec=MockAgentChannel)

    history = [
        ChatMessageContent(role=AuthorRole.SYSTEM, content="test message 1"),
        ChatMessageContent(role=AuthorRole.USER, content="test message 2"),
    ]

    await mock_channel.receive(history)
    mock_channel.receive.assert_called_once_with(history)


async def test_invoke():
    mock_channel = AsyncMock(spec=MockAgentChannel)
    agent = AsyncMock()

    async def async_generator():
        yield ChatMessageContent(role=AuthorRole.SYSTEM, content="test message")

    mock_channel.invoke.return_value = async_generator()

    async for message in mock_channel.invoke(agent):
        assert message.content == "test message"
    mock_channel.invoke.assert_called_once_with(agent)


async def test_get_history():
    mock_channel = AsyncMock(spec=MockAgentChannel)

    async def async_generator():
        yield ChatMessageContent(role=AuthorRole.SYSTEM, content="test history message")

    mock_channel.get_history.return_value = async_generator()

    async for message in mock_channel.get_history():
        assert message.content == "test history message"
    mock_channel.get_history.assert_called_once()
