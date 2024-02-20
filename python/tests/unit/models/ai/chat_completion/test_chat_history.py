# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.models.ai.chat_completion.chat_history import ChatHistory
from semantic_kernel.models.ai.chat_completion.chat_role import ChatRole


@pytest.fixture(scope="function")
def chat_history():
    """Fixture to create a new ChatHistory instance for each test."""
    return ChatHistory()


def test_add_system_message(chat_history):
    content = "System message"
    chat_history.add_system_message(content)
    assert chat_history.messages[-1].content == content
    assert chat_history.messages[-1].role == ChatRole.SYSTEM


def test_add_system_message_at_init(chat_history):
    content = "System message"
    chat_history = ChatHistory(system_message=content)
    assert chat_history.messages[-1].content == content
    assert chat_history.messages[-1].role == ChatRole.SYSTEM


def test_add_user_message(chat_history):
    content = "User message"
    chat_history.add_user_message(content)
    assert chat_history.messages[-1].content == content
    assert chat_history.messages[-1].role == ChatRole.USER


def test_add_assistant_message(chat_history):
    content = "Assistant message"
    chat_history.add_assistant_message(content)
    assert chat_history.messages[-1].content == content
    assert chat_history.messages[-1].role == ChatRole.ASSISTANT


def test_add_tool_message(chat_history):
    content = "Tool message"
    chat_history.add_tool_message(content)
    assert chat_history.messages[-1].content == content
    assert chat_history.messages[-1].role == ChatRole.TOOL


def test_add_message(chat_history):
    content = "Test message"
    role = ChatRole.USER
    encoding = "utf-8"
    chat_history.add_message(message={"role": role, "content": content}, encoding=encoding)
    assert chat_history.messages[-1].content == content
    assert chat_history.messages[-1].role == role
    assert chat_history.messages[-1].encoding == encoding


def test_remove_message(chat_history):
    content = "Message to remove"
    role = ChatRole.USER
    encoding = "utf-8"
    message = ChatMessageContent(role=role, content=content, encoding=encoding)
    chat_history.messages.append(message)
    assert chat_history.remove_message(message) is True
    assert message not in chat_history.messages


def test_len(chat_history):
    content = "Message"
    chat_history.add_user_message(content)
    chat_history.add_system_message(content)
    assert len(chat_history) == 2


def test_getitem(chat_history):
    content = "Message for index"
    chat_history.add_user_message(content)
    assert chat_history[0].content == content


def test_contains(chat_history):
    content = "Message to check"
    role = ChatRole.USER
    encoding = "utf-8"
    message = ChatMessageContent(role=role, content=content, encoding=encoding)
    chat_history.messages.append(message)
    assert message in chat_history


def test_iter(chat_history):
    messages = ["Message 1", "Message 2"]
    for msg in messages:
        chat_history.add_user_message(msg)
    for i, message in enumerate(chat_history):
        assert message.content == messages[i]
