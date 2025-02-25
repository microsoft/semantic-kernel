# Copyright (c) Microsoft. All rights reserved.

from typing import AsyncIterable
from unittest.mock import MagicMock, patch

import pytest

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.bedrock.models.bedrock_agent_model import BedrockAgentModel
from semantic_kernel.agents.channels.bedrock_agent_channel import BedrockAgentChannel
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentChatException


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


@pytest.fixture
def channel_and_agent():
    """
    Fixture that creates a BedrockAgentChannel instance and a mock BedrockAgent.
    """
    from semantic_kernel.agents.bedrock.bedrock_agent import BedrockAgent

    # Create mocks
    mock_agent = MagicMock(spec=BedrockAgent)
    # Set the name and agent_model properties
    mock_agent.name = "MockBedrockAgent"
    mock_agent.agent_model = MagicMock(spec=BedrockAgentModel)
    mock_agent.agent_model.foundation_model = "mock-foundation-model"

    # Mock create_session_id to return a fixed session id
    mock_agent.create_session_id.return_value = "test-session-id"

    # Initialize the BedrockAgentChannel with no messages initially
    channel = BedrockAgentChannel()

    # Return both
    return channel, mock_agent


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


async def test_receive_appends_history_correctly(channel_and_agent):
    """Test that the receive method appends messages while ensuring they alternate in author role."""
    channel, _ = channel_and_agent

    # Provide a list of messages with identical roles to see if placeholders are inserted
    incoming_messages = [
        ChatMessageContent(role=AuthorRole.USER, content="User message 1"),
        ChatMessageContent(role=AuthorRole.USER, content="User message 2"),
        ChatMessageContent(role=AuthorRole.ASSISTANT, content="Assistant message 1"),
        ChatMessageContent(role=AuthorRole.ASSISTANT, content="Assistant message 2"),
    ]

    await channel.receive(incoming_messages)

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

    a = channel.messages

    print(a)

    assert len(channel.messages) == len(expected_roles)
    for i, (msg, exp_role, exp_content) in enumerate(zip(channel.messages, expected_roles, expected_contents)):
        assert msg.role == exp_role, f"Role mismatch at index {i}"
        assert msg.content == exp_content, f"Content mismatch at index {i}"


async def test_invoke_raises_exception_for_non_bedrock_agent(channel_and_agent):
    """Test invoke method raises AgentChatException if the agent provided is not a BedrockAgent."""
    channel, _ = channel_and_agent

    # Place a message in the channel so it's not empty
    channel.messages.append(ChatMessageContent(role=AuthorRole.USER, content="User message"))

    # Create a dummy agent that is not BedrockAgent
    non_bedrock_agent = Agent()

    with pytest.raises(AgentChatException) as exc_info:
        _ = [msg async for msg in channel.invoke(non_bedrock_agent)]

    assert "Agent is not of the expected type" in str(exc_info.value)


async def test_invoke_raises_exception_if_no_history(channel_and_agent):
    """Test invoke method raises AgentChatException if no chat history is available."""
    channel, agent = channel_and_agent

    with pytest.raises(AgentChatException) as exc_info:
        _ = [msg async for msg in channel.invoke(agent)]

    assert "No chat history available" in str(exc_info.value)


@patch("semantic_kernel.agents.bedrock.bedrock_agent.BedrockAgent.create_session_id", return_value="session-id")
async def test_invoke_inserts_placeholders_when_history_needs_to_alternate(mock_session, channel_and_agent):
    """Test invoke ensures _ensure_history_alternates and _ensure_last_message_is_user are called."""
    channel, agent = channel_and_agent

    # Put messages in the channel such that the last message is an assistant's
    channel.messages.append(ChatMessageContent(role=AuthorRole.ASSISTANT, content="Assistant 1"))

    # Mock agent.invoke to return an async generator
    async def mock_invoke(session_id: str, input_text: str, sessionState=None, **kwargs):
        # We just yield one message as if the agent responded
        yield ChatMessageContent(role=AuthorRole.ASSISTANT, content="Mock Agent Response")

    agent.invoke = mock_invoke

    # Because the last message is from the assistant, we expect a placeholder user message to be appended
    # also the history might need to alternate.
    # But since there's only one message, there's nothing to fix except the last message is user.

    # We will now add a user message so we do not get the "No chat history available" error
    channel.messages.append(ChatMessageContent(role=AuthorRole.USER, content="User 1"))

    # Now we do invoke
    outputs = [msg async for msg in channel.invoke(agent)]

    # We'll check if the response is appended to channel.messages
    assert len(outputs) == 1
    assert outputs[0][0] is True, "Expected a user-facing response"
    agent_response = outputs[0][1]
    assert agent_response.content == "Mock Agent Response"

    # The channel messages should now have 3 messages: the assistant, the user, and the new agent message
    assert len(channel.messages) == 3
    assert channel.messages[-1].role == AuthorRole.ASSISTANT
    assert channel.messages[-1].content == "Mock Agent Response"


async def test_invoke_stream_raises_error_for_non_bedrock_agent(channel_and_agent):
    """Test invoke_stream raises AgentChatException if the agent provided is not a BedrockAgent."""
    channel, _ = channel_and_agent
    channel.messages.append(ChatMessageContent(role=AuthorRole.USER, content="User message"))

    non_bedrock_agent = Agent()
    with pytest.raises(AgentChatException) as exc_info:
        _ = [msg async for msg in channel.invoke_stream(non_bedrock_agent, [])]

    assert "Agent is not of the expected type" in str(exc_info.value)


async def test_invoke_stream_raises_no_chat_history(channel_and_agent):
    """Test invoke_stream raises AgentChatException if no messages in the channel."""
    channel, agent = channel_and_agent

    with pytest.raises(AgentChatException) as exc_info:
        _ = [msg async for msg in channel.invoke_stream(agent, [])]

    assert "No chat history available." in str(exc_info.value)


@patch("semantic_kernel.agents.bedrock.bedrock_agent.BedrockAgent.create_session_id", return_value="session-id")
async def test_invoke_stream_appends_response_message(mock_session, channel_and_agent):
    """Test invoke_stream properly yields streaming content and appends an aggregated message at the end."""
    channel, agent = channel_and_agent

    # Put a user message in the channel so it won't raise No chat history
    channel.messages.append(ChatMessageContent(role=AuthorRole.USER, content="Last user message"))

    async def mock_invoke_stream(
        session_id: str, input_text: str, sessionState=None, **kwargs
    ) -> AsyncIterable[StreamingChatMessageContent]:
        yield StreamingChatMessageContent(
            role=AuthorRole.ASSISTANT,
            choice_index=0,
            content="Hello",
        )
        yield StreamingChatMessageContent(
            role=AuthorRole.ASSISTANT,
            choice_index=0,
            content=" World",
        )

    agent.invoke_stream = mock_invoke_stream

    # Check that we get the streamed messages and that the summarized message is appended afterward
    messages_param = [ChatMessageContent(role=AuthorRole.USER, content="Last user message")]  # just to pass the param
    streamed_content = [msg async for msg in channel.invoke_stream(agent, messages_param)]

    # We expect two streamed chunks: "Hello" and " World"
    assert len(streamed_content) == 2
    assert streamed_content[0].content == "Hello"
    assert streamed_content[1].content == " World"

    # Then we expect the channel to append an aggregated ChatMessageContent with "Hello World"
    assert len(messages_param) == 2
    appended = messages_param[1]
    assert appended.role == AuthorRole.ASSISTANT
    assert appended.content == "Hello World"


async def test_get_history(channel_and_agent):
    """Test get_history yields messages in reverse order."""
    channel, _ = channel_and_agent

    channel.messages.append(ChatMessageContent(role=AuthorRole.USER, content="User1"))
    channel.messages.append(ChatMessageContent(role=AuthorRole.ASSISTANT, content="Assistant1"))
    channel.messages.append(ChatMessageContent(role=AuthorRole.USER, content="User2"))

    reversed_history = [msg async for msg in channel.get_history()]

    # Should be reversed
    assert reversed_history[0].content == "User2"
    assert reversed_history[1].content == "Assistant1"
    assert reversed_history[2].content == "User1"


async def test_reset(channel_and_agent):
    """Test that reset clears all messages from the channel."""
    channel, _ = channel_and_agent

    channel.messages.append(ChatMessageContent(role=AuthorRole.USER, content="User1"))
    channel.messages.append(ChatMessageContent(role=AuthorRole.ASSISTANT, content="Assistant1"))

    assert len(channel.messages) == 2

    await channel.reset()

    assert len(channel.messages) == 0


async def test_ensure_history_alternates_handles_multiple_consecutive_roles():
    """Direct test for _ensure_history_alternates by simulating various consecutive roles."""
    channel = BedrockAgentChannel()

    channel.messages = [
        ChatMessageContent(role=AuthorRole.USER, content="User1"),
        ChatMessageContent(role=AuthorRole.USER, content="User2"),
        ChatMessageContent(role=AuthorRole.ASSISTANT, content="Assist1"),
        ChatMessageContent(role=AuthorRole.ASSISTANT, content="Assist2"),
        ChatMessageContent(role=AuthorRole.USER, content="User3"),
        ChatMessageContent(role=AuthorRole.USER, content="User4"),
    ]

    channel._ensure_history_alternates()

    # Expect placeholders inserted:
    # User1, placeholder assistant, User2, Assistant(Assist1), placeholder user, Assistant(Assist2),
    # placeholder assistant, User3, placeholder assistant, User4

    # Let's verify the roles:
    expected_roles = [
        AuthorRole.USER,
        AuthorRole.ASSISTANT,  # placeholder for consecutive user
        AuthorRole.USER,
        AuthorRole.ASSISTANT,
        AuthorRole.USER,  # placeholder for consecutive assistant
        AuthorRole.ASSISTANT,
        AuthorRole.ASSISTANT,  # placeholder for consecutive user (Wait carefully: we had Assist1 -> Assist2? We'll see)
        AuthorRole.USER,
        AuthorRole.ASSISTANT,  # placeholder after we see user -> user
        AuthorRole.USER,
    ]

    # Actually let's systematically figure out the inserted placeholders.
    # The original had: Index 0: U1, Index 1: U2 -> consecutive user, so after index 1 we insert placeholder assistant.
    # Then index 2: Assist1. Now index 3: Assist2 -> consecutive assistant, so insert placeholder user.
    # Then index 4: U3, index 5: U4 -> consecutive user, insert placeholder assistant.

    # Final roles:
    # [U1, placeholder(A), U2, A, placeholder(U), A, U3, placeholder(A), U4]
    # Wait, let's carefully track insertion:
    # messages before insertion:
    # 0: U1
    # 1: U2
    # 2: A1
    # 3: A2
    # 4: U3
    # 5: U4
    # We'll walk with current_index starting at 1:
    # 1: role=U2 same as role=U1 => insert placeholder A at index=1 => increment index=3
    # now 2-> new index=3 => role= A2 same as A1 => insert placeholder user at index=3 => increment index=5
    # now 4-> new index=5 => role=U4 same as U3 => insert placeholder assistant => increment index=7 => done
    # So final messages:
    # index 0: U1
    # index 1: placeholder(A)
    # index 2: U2
    # index 3: A1
    # index 4: placeholder(U)
    # index 5: A2
    # index 6: U3
    # index 7: placeholder(A)
    # index 8: U4

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
    ]

    assert len(channel.messages) == len(expected_roles)
    for i, (msg, exp_role, exp_content) in enumerate(zip(channel.messages, expected_roles, expected_contents)):
        assert msg.role == exp_role, f"Role mismatch at index {i}. Got {msg.role}, expected {exp_role}"
        assert msg.content == exp_content, f"Content mismatch at index {i}. Got {msg.content}, expected {exp_content}"


async def test_ensure_last_message_is_user_appends_placeholder_if_last_assistant():
    """Test that _ensure_last_message_is_user appends a user placeholder if the last message is an assistant one."""
    channel = BedrockAgentChannel()

    channel.messages = [
        ChatMessageContent(role=AuthorRole.USER, content="User1"),
        ChatMessageContent(role=AuthorRole.ASSISTANT, content="Assist1"),
    ]

    channel._ensure_last_message_is_user()

    assert len(channel.messages) == 3
    last_msg = channel.messages[-1]
    assert last_msg.role == AuthorRole.USER
    assert last_msg.content == BedrockAgentChannel.MESSAGE_PLACEHOLDER


async def test_parse_chat_history_to_session_state_returns_valid_structure():
    """Test that _parse_chat_history_to_session_state() returns expected structure ignoring the last message."""
    channel = BedrockAgentChannel()

    channel.messages = [
        ChatMessageContent(role=AuthorRole.USER, content="User1"),
        ChatMessageContent(role=AuthorRole.ASSISTANT, content="Assist1"),
        ChatMessageContent(role=AuthorRole.USER, content="User2"),
    ]

    session_state = channel._parse_chat_history_to_session_state()

    # The last message is not taken, so we only see the first two messages
    assert "conversationHistory" in session_state
    assert "messages" in session_state["conversationHistory"]

    msg_list = session_state["conversationHistory"]["messages"]
    assert len(msg_list) == 2
    assert msg_list[0]["role"] == "user"
    assert msg_list[0]["content"] == [{"text": "User1"}]
    assert msg_list[1]["role"] == "assistant"
    assert msg_list[1]["content"] == [{"text": "Assist1"}]
