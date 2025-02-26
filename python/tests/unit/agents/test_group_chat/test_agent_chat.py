# Copyright (c) Microsoft. All rights reserved.

from unittest import mock
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.agents.group_chat.agent_chat import AgentChat
from semantic_kernel.agents.group_chat.broadcast_queue import ChannelReference
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentChatException


@pytest.fixture
def agent_chat():
    return AgentChat()


@pytest.fixture
def agent():
    mock_agent = MagicMock()
    mock_agent.name = "TestAgent"
    return mock_agent


@pytest.fixture
def chat_message():
    mock_chat_message = MagicMock(spec=ChatMessageContent)
    mock_chat_message.role = "user"
    return mock_chat_message


async def test_set_activity_or_throw_when_inactive(agent_chat):
    agent_chat._is_active = False
    agent_chat.set_activity_or_throw()
    assert agent_chat.is_active


async def test_set_activity_or_throw_when_active(agent_chat):
    agent_chat._is_active = True
    with pytest.raises(Exception, match="Unable to proceed while another agent is active."):
        agent_chat.set_activity_or_throw()


async def test_clear_activity_signal(agent_chat):
    agent_chat._is_active = True
    agent_chat.clear_activity_signal()
    assert not agent_chat.is_active


async def test_get_messages_in_descending_order(agent_chat, chat_message):
    agent_chat.history.messages = [chat_message, chat_message, chat_message]
    messages = []
    async for message in agent_chat.get_messages_in_descending_order():
        messages.append(message)
    assert len(messages) == 3


async def test_get_chat_messages_without_agent(agent_chat, chat_message):
    agent_chat.history.messages = [chat_message]
    with patch(
        "semantic_kernel.agents.group_chat.agent_chat.AgentChat.get_messages_in_descending_order",
        return_value=AsyncMock(),
    ) as mock_get_messages:
        async for _ in agent_chat.get_chat_messages():
            pass
        mock_get_messages.assert_called_once()


async def test_get_chat_messages_with_agent(agent_chat, agent, chat_message):
    agent_chat.channel_map[agent] = "test_channel"

    mock_channel = mock.MagicMock(spec=AgentChannel)
    agent_chat.agent_channels["test_channel"] = mock_channel

    with (
        patch("semantic_kernel.agents.group_chat.agent_chat.AgentChat._get_agent_hash", return_value="test_channel"),
        patch("semantic_kernel.agents.group_chat.agent_chat.AgentChat._synchronize_channel", return_value=mock_channel),
        patch.object(mock_channel, "get_history", return_value=AsyncMock()),
    ):
        async for _ in agent_chat.get_chat_messages(agent):
            pass


async def test_add_chat_message(agent_chat, chat_message):
    with patch(
        "semantic_kernel.agents.group_chat.agent_chat.AgentChat.add_chat_messages",
        return_value=AsyncMock(),
    ) as mock_add_chat_messages:
        await agent_chat.add_chat_message(chat_message)
        mock_add_chat_messages.assert_called_once_with([chat_message])


async def test_add_chat_messages(agent_chat, chat_message):
    with patch("semantic_kernel.agents.group_chat.broadcast_queue.BroadcastQueue.enqueue", return_value=AsyncMock()):
        await agent_chat.add_chat_messages([chat_message])
        assert chat_message in agent_chat.history.messages


async def test_invoke_agent(agent_chat, agent, chat_message):
    mock_channel = mock.MagicMock(spec=AgentChannel)

    async def mock_invoke(*args, **kwargs):
        yield True, chat_message

    mock_channel.invoke.side_effect = mock_invoke

    with (
        patch(
            "semantic_kernel.agents.group_chat.agent_chat.AgentChat._get_or_create_channel", return_value=mock_channel
        ),
        patch(
            "semantic_kernel.agents.group_chat.broadcast_queue.BroadcastQueue.enqueue",
            return_value=AsyncMock(),
        ),
    ):
        async for _ in agent_chat.invoke_agent(agent):
            pass

    mock_channel.invoke.assert_called_once_with(agent)
    await agent_chat.reset()


async def test_invoke_streaming_agent(agent_chat, agent, chat_message):
    mock_channel = mock.MagicMock(spec=AgentChannel)

    async def mock_invoke(*args, **kwargs):
        yield chat_message

    mock_channel.invoke_stream.side_effect = mock_invoke

    with (
        patch(
            "semantic_kernel.agents.group_chat.agent_chat.AgentChat._get_or_create_channel", return_value=mock_channel
        ),
        patch(
            "semantic_kernel.agents.group_chat.broadcast_queue.BroadcastQueue.enqueue",
            return_value=AsyncMock(),
        ),
    ):
        async for _ in agent_chat.invoke_agent_stream(agent):
            pass

    mock_channel.invoke_stream.assert_called_once_with(agent, [])
    await agent_chat.reset()


async def test_synchronize_channel_with_existing_channel(agent_chat):
    mock_channel = MagicMock(spec=AgentChannel)
    channel_key = "test_channel_key"
    agent_chat.agent_channels[channel_key] = mock_channel

    with patch(
        "semantic_kernel.agents.group_chat.broadcast_queue.BroadcastQueue.ensure_synchronized", return_value=AsyncMock()
    ) as mock_ensure_synchronized:
        result = await agent_chat._synchronize_channel(channel_key)

        assert result == mock_channel
        mock_ensure_synchronized.assert_called_once_with(ChannelReference(channel=mock_channel, hash=channel_key))


async def test_synchronize_channel_with_nonexistent_channel(agent_chat):
    channel_key = "test_channel_key"

    result = await agent_chat._synchronize_channel(channel_key)

    assert result is None


def test_get_agent_hash_with_existing_hash(agent_chat, agent):
    expected_hash = "existing_hash"
    agent_chat.channel_map[agent] = expected_hash

    result = agent_chat._get_agent_hash(agent)

    assert result == expected_hash


def test_get_agent_hash_generates_new_hash(agent_chat, agent):
    expected_hash = "new_hash"
    agent.get_channel_keys = MagicMock(return_value=["key1", "key2"])

    with patch(
        "semantic_kernel.agents.group_chat.agent_chat.KeyEncoder.generate_hash", return_value=expected_hash
    ) as mock_generate_hash:
        result = agent_chat._get_agent_hash(agent)

        assert result == expected_hash
        mock_generate_hash.assert_called_once_with(["key1", "key2"])
        assert agent_chat.channel_map[agent] == expected_hash


async def test_add_chat_messages_throws_exception_for_system_role(agent_chat):
    system_message = MagicMock(spec=ChatMessageContent)
    system_message.role = AuthorRole.SYSTEM

    with pytest.raises(AgentChatException, match="System messages cannot be added to the chat history."):
        await agent_chat.add_chat_messages([system_message])


async def test_get_or_create_channel_creates_new_channel(agent_chat, agent):
    agent_chat.history.messages = [MagicMock(spec=ChatMessageContent)]
    channel_key = "test_channel_key"
    mock_channel = AsyncMock(spec=AgentChannel)

    with (
        patch(
            "semantic_kernel.agents.group_chat.agent_chat.AgentChat._get_agent_hash", return_value=channel_key
        ) as mock_get_agent_hash,
        patch(
            "semantic_kernel.agents.group_chat.agent_chat.AgentChat._synchronize_channel", return_value=None
        ) as mock_synchronize_channel,
    ):
        agent.create_channel = AsyncMock(return_value=mock_channel)
        with patch.object(mock_channel, "receive", return_value=AsyncMock()) as mock_receive:
            result = await agent_chat._get_or_create_channel(agent)

            assert result == mock_channel
            mock_get_agent_hash.assert_called_once_with(agent)
            mock_synchronize_channel.assert_called_once_with(channel_key)
            agent.create_channel.assert_called_once()
            mock_receive.assert_called_once_with(agent_chat.history.messages)
            assert agent_chat.agent_channels[channel_key] == mock_channel


async def test_get_or_create_channel_reuses_existing_channel(agent_chat, agent):
    channel_key = "test_channel_key"
    mock_channel = MagicMock(spec=AgentChannel)

    with (
        patch(
            "semantic_kernel.agents.group_chat.agent_chat.AgentChat._get_agent_hash", return_value=channel_key
        ) as mock_get_agent_hash,
        patch(
            "semantic_kernel.agents.group_chat.agent_chat.AgentChat._synchronize_channel", return_value=mock_channel
        ) as mock_synchronize_channel,
    ):
        result = await agent_chat._get_or_create_channel(agent)

        assert result == mock_channel
        mock_get_agent_hash.assert_called_once_with(agent)
        mock_synchronize_channel.assert_called_once_with(channel_key)
        agent.create_channel.assert_not_called()
