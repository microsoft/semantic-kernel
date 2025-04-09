# Copyright (c) Microsoft. All rights reserved.

from collections.abc import AsyncIterable
from unittest.mock import MagicMock, Mock, patch

import boto3
import pytest

from semantic_kernel.agents.agent import Agent, AgentResponseItem, AgentThread
from semantic_kernel.agents.bedrock.models.bedrock_agent_model import BedrockAgentModel
from semantic_kernel.agents.channels.bedrock_agent_channel import BedrockAgentChannel
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentChatException


@pytest.fixture
@patch.object(boto3, "client", return_value=Mock())
def mock_channel(client):
    from semantic_kernel.agents.bedrock.bedrock_agent import BedrockAgentThread

    BedrockAgentChannel.model_rebuild()
    thread = BedrockAgentThread(client, session_id="test_session_id")

    return BedrockAgentChannel(thread=thread)


class ConcreteAgent(Agent):
    async def get_response(self, *args, **kwargs) -> ChatMessageContent:
        raise NotImplementedError

    def invoke(self, *args, **kwargs) -> AsyncIterable[ChatMessageContent]:
        raise NotImplementedError

    def invoke_stream(self, *args, **kwargs) -> AsyncIterable[StreamingChatMessageContent]:
        raise NotImplementedError


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


@pytest.fixture
def mock_agent():
    """
    Fixture that creates a mock BedrockAgent.
    """
    from semantic_kernel.agents.bedrock.bedrock_agent import BedrockAgent

    # Create mocks
    mock_agent = MagicMock(spec=BedrockAgent)
    # Set the name and agent_model properties
    mock_agent.name = "MockBedrockAgent"
    mock_agent.agent_model = MagicMock(spec=BedrockAgentModel)
    mock_agent.agent_model.foundation_model = "mock-foundation-model"

    return mock_agent


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
    assert len(mock_channel.messages) == len(chat_history)
    await mock_channel.reset()
    assert len(mock_channel) == 0
    assert len(mock_channel.messages) == 0


async def test_receive_appends_history_correctly(mock_channel):
    """Test that the receive method appends messages while ensuring they alternate in author role."""
    # Provide a list of messages with identical roles to see if placeholders are inserted
    incoming_messages = [
        ChatMessageContent(role=AuthorRole.USER, content="User message 1"),
        ChatMessageContent(role=AuthorRole.USER, content="User message 2"),
        ChatMessageContent(role=AuthorRole.ASSISTANT, content="Assistant message 1"),
        ChatMessageContent(role=AuthorRole.ASSISTANT, content="Assistant message 2"),
    ]

    await mock_channel.receive(incoming_messages)

    # The final channel.messages should be:
    # user message 1, user placeholder, user message 2, assistant placeholder, assistant message 1,
    # assistant placeholder, assistant message 2
    expected_roles = [
        AuthorRole.USER,
        AuthorRole.ASSISTANT,  # placeholder
        AuthorRole.USER,
        AuthorRole.ASSISTANT,
        AuthorRole.USER,  # placeholder
        AuthorRole.ASSISTANT,
    ]
    expected_contents = [
        "User message 1",
        BedrockAgentChannel.MESSAGE_PLACEHOLDER,
        "User message 2",
        "Assistant message 1",
        BedrockAgentChannel.MESSAGE_PLACEHOLDER,
        "Assistant message 2",
    ]

    assert len(mock_channel.messages) == len(expected_roles)
    for i, (msg, exp_role, exp_content) in enumerate(zip(mock_channel.messages, expected_roles, expected_contents)):
        assert msg.role == exp_role, f"Role mismatch at index {i}"
        assert msg.content == exp_content, f"Content mismatch at index {i}"


async def test_invoke_raises_exception_for_non_bedrock_agent(mock_channel):
    """Test invoke method raises AgentChatException if the agent provided is not a BedrockAgent."""
    # Place a message in the channel so it's not empty
    mock_channel.messages.append(ChatMessageContent(role=AuthorRole.USER, content="User message"))

    # Create a dummy agent that is not BedrockAgent
    non_bedrock_agent = ConcreteAgent()

    with pytest.raises(AgentChatException) as exc_info:
        _ = [msg async for msg in mock_channel.invoke(non_bedrock_agent)]

    assert "Agent is not of the expected type" in str(exc_info.value)


async def test_invoke_raises_exception_if_no_history(mock_channel, mock_agent):
    """Test invoke method raises AgentChatException if no chat history is available."""
    with pytest.raises(AgentChatException) as exc_info:
        _ = [msg async for msg in mock_channel.invoke(mock_agent)]

    assert "No chat history available" in str(exc_info.value)


async def test_invoke_inserts_placeholders_when_history_needs_to_alternate(mock_channel, mock_agent):
    """Test invoke ensures _ensure_history_alternates and _ensure_last_message_is_user are called."""
    # Put messages in the channel such that the last message is an assistant's
    mock_channel.messages.append(ChatMessageContent(role=AuthorRole.ASSISTANT, content="Assistant 1"))

    # Mock agent.invoke to return an async generator
    async def mock_invoke(messages: str, thread: AgentThread, sessionState=None, **kwargs):
        # We just yield one message as if the agent responded
        yield AgentResponseItem(
            message=ChatMessageContent(role=AuthorRole.ASSISTANT, content="Mock Agent Response"),
            thread=mock_channel.thread,
        )

    mock_agent.invoke = mock_invoke

    # Because the last message is from the assistant, we expect a placeholder user message to be appended
    # also the history might need to alternate.
    # But since there's only one message, there's nothing to fix except the last message is user.

    # We will now add a user message so we do not get the "No chat history available" error
    mock_channel.messages.append(ChatMessageContent(role=AuthorRole.USER, content="User 1"))

    # Now we do invoke
    outputs = [msg async for msg in mock_channel.invoke(mock_agent)]

    # We'll check if the response is appended to channel.messages
    assert len(outputs) == 1
    assert outputs[0][0] is True, "Expected a user-facing response"
    agent_response = outputs[0][1]
    assert agent_response.content == "Mock Agent Response"

    # The channel messages should now have 3 messages: the assistant, the user, and the new agent message
    assert len(mock_channel.messages) == 3
    assert mock_channel.messages[-1].role == AuthorRole.ASSISTANT
    assert mock_channel.messages[-1].content == "Mock Agent Response"


async def test_invoke_stream_raises_error_for_non_bedrock_agent(mock_channel):
    """Test invoke_stream raises AgentChatException if the agent provided is not a BedrockAgent."""
    mock_channel.messages.append(ChatMessageContent(role=AuthorRole.USER, content="User message"))

    non_bedrock_agent = ConcreteAgent()

    with pytest.raises(AgentChatException) as exc_info:
        _ = [msg async for msg in mock_channel.invoke_stream(non_bedrock_agent, [])]

    assert "Agent is not of the expected type" in str(exc_info.value)


async def test_invoke_stream_raises_no_chat_history(mock_channel, mock_agent):
    """Test invoke_stream raises AgentChatException if no messages in the channel."""

    with pytest.raises(AgentChatException) as exc_info:
        _ = [msg async for msg in mock_channel.invoke_stream(mock_agent, [])]

    assert "No chat history available." in str(exc_info.value)


async def test_invoke_stream_appends_response_message(mock_channel, mock_agent):
    """Test invoke_stream properly yields streaming content and appends an aggregated message at the end."""
    # Put a user message in the channel so it won't raise No chat history
    mock_channel.messages.append(ChatMessageContent(role=AuthorRole.USER, content="Last user message"))

    async def mock_invoke_stream(
        messages: str, thread: AgentThread, sessionState=None, **kwargs
    ) -> AsyncIterable[StreamingChatMessageContent]:
        yield AgentResponseItem(
            message=StreamingChatMessageContent(
                role=AuthorRole.ASSISTANT,
                choice_index=0,
                content="Hello",
            ),
            thread=mock_channel.thread,
        )
        yield AgentResponseItem(
            message=StreamingChatMessageContent(
                role=AuthorRole.ASSISTANT,
                choice_index=0,
                content=" World",
            ),
            thread=mock_channel.thread,
        )

    mock_agent.invoke_stream = mock_invoke_stream

    # Check that we get the streamed messages and that the summarized message is appended afterward
    messages_param = [ChatMessageContent(role=AuthorRole.USER, content="Last user message")]  # just to pass the param
    streamed_content = [msg async for msg in mock_channel.invoke_stream(mock_agent, messages_param)]

    # We expect two streamed chunks: "Hello" and " World"
    assert len(streamed_content) == 2
    assert streamed_content[0].content == "Hello"
    assert streamed_content[1].content == " World"

    # Then we expect the channel to append an aggregated ChatMessageContent with "Hello World"
    assert len(messages_param) == 2
    appended = messages_param[1]
    assert appended.role == AuthorRole.ASSISTANT
    assert appended.content == "Hello World"


async def test_get_history(mock_channel, chat_history):
    """Test get_history yields messages in reverse order."""

    mock_channel.messages = chat_history

    reversed_history = [msg async for msg in mock_channel.get_history()]

    # Should be reversed
    assert reversed_history[0].content == "I'm good, thank you!"
    assert reversed_history[1].content == "How are you?"
    assert reversed_history[2].content == "Hello, User!"
    assert reversed_history[3].content == "Hello, Bedrock!"


async def test_invoke_alternates_history_and_ensures_last_user_message(mock_channel, mock_agent):
    """Test invoke method ensures history alternates and last message is user."""
    mock_channel.messages = [
        ChatMessageContent(role=AuthorRole.USER, content="User1"),
        ChatMessageContent(role=AuthorRole.USER, content="User2"),
        ChatMessageContent(role=AuthorRole.ASSISTANT, content="Assist1"),
        ChatMessageContent(role=AuthorRole.ASSISTANT, content="Assist2"),
        ChatMessageContent(role=AuthorRole.USER, content="User3"),
        ChatMessageContent(role=AuthorRole.USER, content="User4"),
        ChatMessageContent(role=AuthorRole.ASSISTANT, content="Assist3"),
    ]

    async for _, msg in mock_channel.invoke(mock_agent):
        pass

    # let's define expected roles from that final structure:
    expected_roles = [
        AuthorRole.USER,
        AuthorRole.ASSISTANT,  # placeholder
        AuthorRole.USER,
        AuthorRole.ASSISTANT,
        AuthorRole.USER,  # placeholder
        AuthorRole.ASSISTANT,
        AuthorRole.USER,
        AuthorRole.ASSISTANT,  # placeholder
        AuthorRole.USER,
        AuthorRole.ASSISTANT,
        AuthorRole.USER,  # placeholder
    ]
    expected_contents = [
        "User1",
        BedrockAgentChannel.MESSAGE_PLACEHOLDER,
        "User2",
        "Assist1",
        BedrockAgentChannel.MESSAGE_PLACEHOLDER,
        "Assist2",
        "User3",
        BedrockAgentChannel.MESSAGE_PLACEHOLDER,
        "User4",
        "Assist3",
        BedrockAgentChannel.MESSAGE_PLACEHOLDER,
    ]

    assert len(mock_channel.messages) == len(expected_roles)
    for i, (msg, exp_role, exp_content) in enumerate(zip(mock_channel.messages, expected_roles, expected_contents)):
        assert msg.role == exp_role, f"Role mismatch at index {i}. Got {msg.role}, expected {exp_role}"
        assert msg.content == exp_content, f"Content mismatch at index {i}. Got {msg.content}, expected {exp_content}"
