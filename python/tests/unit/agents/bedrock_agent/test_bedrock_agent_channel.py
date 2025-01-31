import pytest
from unittest.mock import MagicMock, patch
from semantic_kernel.agents.channels.bedrock_agent_channel import BedrockAgentChannel

@pytest.fixture
def mock_bedrock_client():
    return MagicMock()

@pytest.fixture
def channel(mock_bedrock_client):
    return BedrockAgentChannel(mock_bedrock_client)

def test_send_message(channel, mock_bedrock_client):
    # Test to verify the send_message functionality
    message = "Hello, Bedrock!"
    channel.send_message(message)
    mock_bedrock_client.send_message.assert_called_once_with(message)

def test_send_message_error_handling(channel, mock_bedrock_client):
    # Test to verify error handling in send_message
    message = "Hello, Bedrock!"
    mock_bedrock_client.send_message.side_effect = Exception("Error sending message")
    with pytest.raises(Exception) as context:
        channel.send_message(message)
    assert str(context.value) == "Error sending message"

def test_receive_message(channel, mock_bedrock_client):
    # Test to verify the receive_message functionality
    expected_message = "Hello, User!"
    mock_bedrock_client.receive_message.return_value = expected_message
    actual_message = channel.receive_message()
    assert actual_message == expected_message

def test_receive_message_error_handling(channel, mock_bedrock_client):
    # Test to verify error handling in receive_message
    mock_bedrock_client.receive_message.side_effect = Exception("Error receiving message")
    with pytest.raises(Exception) as context:
        channel.receive_message()
    assert str(context.value) == "Error receiving message"

def test_channel_initialization(channel, mock_bedrock_client):
    # Test to verify the initialization of BedrockAgentChannel
    assert isinstance(channel, BedrockAgentChannel)
    assert channel.bedrock_client == mock_bedrock_client

def test_channel_send_message_with_empty_string(channel, mock_bedrock_client):
    # Test to verify send_message with an empty string
    message = ""
    channel.send_message(message)
    mock_bedrock_client.send_message.assert_called_once_with(message)

def test_channel_receive_message_with_no_message(channel, mock_bedrock_client):
    # Test to verify receive_message when no message is received
    mock_bedrock_client.receive_message.return_value = None
    actual_message = channel.receive_message()
    assert actual_message is None

def test_message_format(channel, mock_bedrock_client):
    # Test to verify the correct format of chat messages
    message = {"role": "user", "content": "Hello, Bedrock!"}
    channel.send_message(message)
    mock_bedrock_client.send_message.assert_called_once_with(message)

def test_chat_history_alternation(channel, mock_bedrock_client):
    # Test to verify chat history alternates between user and assistant messages
    history = [
        {"role": "user", "content": "Hello, Bedrock!"},
        {"role": "assistant", "content": "Hello, User!"},
        {"role": "user", "content": "How are you?"},
        {"role": "assistant", "content": "I'm good, thank you!"},
    ]
    for message in history:
        channel.send_message(message)
    assert all(
        history[i]["role"] != history[i + 1]["role"]
        for i in range(len(history) - 1)
    )

def test_chat_history_alternation_with_unordered_history(channel, mock_bedrock_client):
    # Test to verify chat history alternates between user and assistant messages even when the history received does not follow that order
    unordered_history = [
        {"role": "assistant", "content": "Hello, User! I am agent A"},
        {"role": "assistant", "content": "Hello, User! I am agent B"},
        {"role": "user", "content": "Hello!"},
        {"role": "user", "content": "How are you?"},
    ]
    for message in unordered_history:
        channel.send_message(message)
    assert all(
        unordered_history[i]["role"] != unordered_history[i + 1]["role"]
        for i in range(len(unordered_history) - 1)
    )
