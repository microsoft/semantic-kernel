# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.contents.chat_message_content import ChatMessageContent


@pytest.fixture
def mock_channel():
    from semantic_kernel.agents.channels.bedrock_agent_channel import BedrockAgentChannel

    return BedrockAgentChannel()


@pytest.fixture
def chat_history() -> list[ChatMessageContent]:
    return [
        ChatMessageContent(role="user", content="Hello, Bedrock!"),
        ChatMessageContent(role="assistant", content="Hello, User!"),
        ChatMessageContent(role="user", content="How are you?"),
        ChatMessageContent(role="assistant", content="I'm good, thank you!"),
    ]


@pytest.fixture
def chat_history_not_alternate_role() -> list[ChatMessageContent]:
    return [
        ChatMessageContent(role="user", content="Hello, Bedrock!"),
        ChatMessageContent(role="user", content="Hello, User!"),
        ChatMessageContent(role="assistant", content="How are you?"),
        ChatMessageContent(role="assistant", content="I'm good, thank you!"),
    ]


async def test_receive_message(mock_channel, chat_history):
    # Test to verify the receive_message functionality
    await mock_channel.receive(chat_history)
    assert len(mock_channel) == len(chat_history)


async def test_channel_receive_message_with_no_message(mock_channel):
    # Test to verify receive_message when no message is received
    await mock_channel.receive([])
    assert len(mock_channel) == 0


async def test_chat_history_alternation(mock_channel, chat_history_not_alternate_role):
    # Test to verify chat history alternates between user and assistant messages
    await mock_channel.receive(chat_history_not_alternate_role)
    assert all(
        mock_channel.messages[i].role != mock_channel.messages[i + 1].role
        for i in range(len(chat_history_not_alternate_role) - 1)
    )
    assert mock_channel.messages[1].content == mock_channel.MESSAGE_PLACEHOLDER
    assert mock_channel.messages[4].content == mock_channel.MESSAGE_PLACEHOLDER


async def test_channel_reset(mock_channel, chat_history):
    # Test to verify the reset functionality
    await mock_channel.receive(chat_history)
    assert len(mock_channel) == len(chat_history)
    await mock_channel.reset()
    assert len(mock_channel) == 0
