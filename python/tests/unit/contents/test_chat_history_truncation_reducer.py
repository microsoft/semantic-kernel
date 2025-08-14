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
    # We expect only 2 messages remain after truncation
    assert result is not None
    assert len(result) == 2
    # They should be the last 4 messages while tool result is not orphaned
    assert result[0] == chat_messages[-2]
    assert result[1] == chat_messages[-1]


async def test_truncation_reducer_truncation_with_tools(chat_messages_with_tools):
    # Force a smaller target so we do need to reduce
    reducer = ChatHistoryTruncationReducer(target_count=3, threshold_count=0)
    reducer.messages = chat_messages_with_tools
    result = await reducer.reduce()
    # We expect 4 messages remain after truncation
    # Tool results are not orphaned, so we expect to keep them
    assert result is not None
    assert len(result) == 4
    # They should be the last 4 messages
    assert result[0] == chat_messages_with_tools[-4]
    assert result[1] == chat_messages_with_tools[-3]
    assert result[2] == chat_messages_with_tools[-2]
    assert result[3] == chat_messages_with_tools[-1]
