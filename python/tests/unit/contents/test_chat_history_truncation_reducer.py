# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.history_reducer.chat_history_truncation_reducer import ChatHistoryTruncationReducer
from semantic_kernel.contents.utils.author_role import AuthorRole


@pytest.fixture
def chat_messages():
    msgs = []
    msgs.append(ChatMessageContent(role=AuthorRole.SYSTEM, content="System message."))
    msgs.append(ChatMessageContent(role=AuthorRole.USER, content="User message 1"))
    msgs.append(ChatMessageContent(role=AuthorRole.ASSISTANT, content="Assistant message 1"))
    msgs.append(ChatMessageContent(role=AuthorRole.USER, content="User message 2"))
    msgs.append(ChatMessageContent(role=AuthorRole.ASSISTANT, content="Assistant message 2"))
    return msgs


@pytest.fixture
def chat_messages_with_tools():
    return [
        ChatMessageContent(role=AuthorRole.SYSTEM, content="System message."),
        ChatMessageContent(role=AuthorRole.USER, content="User message 1"),
        ChatMessageContent(
            role=AuthorRole.ASSISTANT,
            items=[FunctionCallContent(id="123", function_name="search", plugin_name="plugin", arguments={"q": "x"})],
        ),
        ChatMessageContent(
            role=AuthorRole.TOOL,
            items=[FunctionResultContent(id="123", function_name="search", plugin_name="plugin", result="RESULT")],
        ),
        ChatMessageContent(role=AuthorRole.USER, content="User message 2"),
        ChatMessageContent(role=AuthorRole.ASSISTANT, content="Assistant message 2"),
    ]


def test_truncation_reducer_init():
    reducer = ChatHistoryTruncationReducer(target_count=5, threshold_count=2)
    assert reducer.target_count == 5
    assert reducer.threshold_count == 2


def test_truncation_reducer_defaults():
    reducer = ChatHistoryTruncationReducer(target_count=5)
    assert reducer.threshold_count == 0


def test_truncation_reducer_eq_and_hash():
    r1 = ChatHistoryTruncationReducer(target_count=5, threshold_count=2)
    r2 = ChatHistoryTruncationReducer(target_count=5, threshold_count=2)
    r3 = ChatHistoryTruncationReducer(target_count=5, threshold_count=1)
    assert r1 == r2
    assert r1 != r3
    assert hash(r1) == hash(r2)
    assert hash(r1) != hash(r3)


async def test_truncation_reducer_no_need(chat_messages):
    # If total <= target + threshold => returns None
    reducer = ChatHistoryTruncationReducer(target_count=5, threshold_count=0)
    result = await reducer.reduce()
    assert result is None


async def test_truncation_reducer_no_truncation_index_found():
    # If the safe reduction index < 0, returns None
    # We'll craft a scenario where the number of messages is big,
    # but the function can't find a safe index to cut
    msgs = [ChatMessageContent(role=AuthorRole.USER, content="Msg")] * 10
    # Suppose threshold_count is huge, so effectively we can't reduce
    reducer = ChatHistoryTruncationReducer(target_count=3, threshold_count=10)
    reducer.messages = msgs
    result = await reducer.reduce()
    assert result is None


async def test_truncation_reducer_truncation(chat_messages):
    # Force a smaller target so we do need to reduce
    reducer = ChatHistoryTruncationReducer(target_count=2)
    reducer.messages = chat_messages
    result = await reducer.reduce()
    # We expect 2 messages: system message is preserved + 1 conversation message
    # (target_count=2 includes the system message, matching .NET SDK behavior)
    assert result is not None
    assert len(result) == 2
    # System message should be first, followed by the last conversation message
    assert result[0] == chat_messages[0]  # System message preserved
    assert result[0].role == AuthorRole.SYSTEM
    assert result[1] == chat_messages[-1]


async def test_truncation_reducer_truncation_with_tools(chat_messages_with_tools):
    # Force a smaller target so we do need to reduce
    reducer = ChatHistoryTruncationReducer(target_count=3, threshold_count=0)
    reducer.messages = chat_messages_with_tools
    result = await reducer.reduce()
    # We expect 3 messages: system message + last 2 conversation messages
    # (target_count=3 includes the system message, matching .NET SDK behavior)
    assert result is not None
    assert len(result) == 3
    # System message preserved, followed by last user-assistant pair
    assert result[0] == chat_messages_with_tools[0]  # System message
    assert result[0].role == AuthorRole.SYSTEM
    assert result[1] == chat_messages_with_tools[-2]  # User message 2
    assert result[2] == chat_messages_with_tools[-1]  # Assistant message 2


async def test_truncation_preserves_system_message():
    """Verify that the system message is preserved after truncation (issue #12612)."""
    reducer = ChatHistoryTruncationReducer(
        target_count=2,
        system_message="a system message",
    )
    reducer.add_message(ChatMessageContent(role=AuthorRole.USER, content="user prompt 1"))
    reducer.add_message(ChatMessageContent(role=AuthorRole.ASSISTANT, content="response 1"))
    reducer.add_message(ChatMessageContent(role=AuthorRole.USER, content="user prompt 2"))
    reducer.add_message(ChatMessageContent(role=AuthorRole.ASSISTANT, content="response 2"))
    reducer.add_message(ChatMessageContent(role=AuthorRole.USER, content="user prompt 3"))
    reducer.add_message(ChatMessageContent(role=AuthorRole.ASSISTANT, content="response 3"))
    reducer.add_message(ChatMessageContent(role=AuthorRole.USER, content="user prompt 4"))
    reducer.add_message(ChatMessageContent(role=AuthorRole.ASSISTANT, content="response 4"))

    result = await reducer.reduce()
    assert result is not None

    # System message must be present after reduction
    roles = [msg.role for msg in result.messages]
    assert AuthorRole.SYSTEM in roles, "System message was deleted by the history reducer"
    assert result.messages[0].role == AuthorRole.SYSTEM
    assert result.messages[0].content == "a system message"


async def test_truncation_preserves_developer_message():
    """Verify that developer messages are preserved after truncation."""
    msgs = [
        ChatMessageContent(role=AuthorRole.DEVELOPER, content="Developer instructions."),
        ChatMessageContent(role=AuthorRole.USER, content="User message 1"),
        ChatMessageContent(role=AuthorRole.ASSISTANT, content="Assistant message 1"),
        ChatMessageContent(role=AuthorRole.USER, content="User message 2"),
        ChatMessageContent(role=AuthorRole.ASSISTANT, content="Assistant message 2"),
    ]
    reducer = ChatHistoryTruncationReducer(target_count=2)
    reducer.messages = msgs
    result = await reducer.reduce()
    assert result is not None
    assert len(result) == 2
    # Developer message should be first
    assert result[0].role == AuthorRole.DEVELOPER
    assert result[0].content == "Developer instructions."


async def test_truncation_target_count_1_with_system_message():
    """Verify target_count=1 with system message does not crash (edge case from review)."""
    reducer = ChatHistoryTruncationReducer(target_count=1, system_message="System prompt")
    reducer.add_message(ChatMessageContent(role=AuthorRole.USER, content="Hello"))
    reducer.add_message(ChatMessageContent(role=AuthorRole.ASSISTANT, content="Hi"))
    reducer.add_message(ChatMessageContent(role=AuthorRole.USER, content="How are you?"))
    reducer.add_message(ChatMessageContent(role=AuthorRole.ASSISTANT, content="Good"))

    # Should not crash. Either returns None (no reduction possible)
    # or returns just the system message.
    result = await reducer.reduce()
    if result is not None:
        # System message must be preserved
        assert any(m.role == AuthorRole.SYSTEM for m in result.messages)


async def test_truncation_without_system_message():
    """Verify truncation works correctly when there is no system message."""
    msgs = [
        ChatMessageContent(role=AuthorRole.USER, content="User message 1"),
        ChatMessageContent(role=AuthorRole.ASSISTANT, content="Assistant message 1"),
        ChatMessageContent(role=AuthorRole.USER, content="User message 2"),
        ChatMessageContent(role=AuthorRole.ASSISTANT, content="Assistant message 2"),
    ]
    reducer = ChatHistoryTruncationReducer(target_count=2)
    reducer.messages = msgs
    result = await reducer.reduce()
    assert result is not None
    assert len(result) == 2
    assert result[0] == msgs[-2]
    assert result[1] == msgs[-1]
