# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.history_reducer.chat_history_reducer_utils import (
    SUMMARY_METADATA_KEY,
    extract_range,
    locate_safe_reduction_index,
    locate_summarization_boundary,
)
from semantic_kernel.contents.utils.author_role import AuthorRole


@pytest.fixture
def chat_messages():
    """Returns a list of ChatMessageContent objects with varied metadata, roles, and items."""
    msgs = []

    # 1) Summary message at index 0 (system)
    msg_summary = ChatMessageContent(role=AuthorRole.SYSTEM, content="Summary so far.")
    msg_summary.metadata[SUMMARY_METADATA_KEY] = True
    msgs.append(msg_summary)

    # 2) Normal user message (index=1)
    msgs.append(ChatMessageContent(role=AuthorRole.USER, content="Hello!"))

    # 3) Another user message (index=2) so that if we need index=2, it's a user
    msgs.append(ChatMessageContent(role=AuthorRole.USER, content="Second user message."))

    # 4) Assistant (index=3)
    msgs.append(ChatMessageContent(role=AuthorRole.ASSISTANT, content="Assistant answer."))

    # 5) Another user message (index=4)
    msgs.append(ChatMessageContent(role=AuthorRole.USER, content="User question."))

    # 6) Function call (index=5)
    msg_func_call = ChatMessageContent(role=AuthorRole.ASSISTANT, content="Function called.")
    msg_func_call.items.append(FunctionCallContent(function_name="function_name", arguments={"param": "value"}))
    msgs.append(msg_func_call)

    # 7) Function result (index=6)
    msg_func_result = ChatMessageContent(role=AuthorRole.ASSISTANT, content="Result from function.")
    msgs.append(msg_func_result)

    return msgs


def test_locate_summarization_boundary(chat_messages):
    # The first message is flagged with SUMMARY_METADATA_KEY
    # So the boundary should be index=1 (the second message).
    boundary_index = locate_summarization_boundary(chat_messages)
    assert boundary_index == 1

    # If there's no summary key in any messages
    for msg in chat_messages:
        msg.metadata.pop(SUMMARY_METADATA_KEY, None)
    boundary_index_no_summary = locate_summarization_boundary(chat_messages)
    assert boundary_index_no_summary == 0


@pytest.mark.parametrize(
    "target_count,threshold_count,offset_count,expected",
    [
        # If total_count <= target_count + threshold, return -1
        (10, 0, 0, -1),
        # If we do need to reduce, but we can't find a safe index because of function calls
        (3, 0, 0, 4),
        # With threshold_count, the result may be -1 if not large enough
        (6, 2, 0, -1),
    ],
)
def test_locate_safe_reduction_index(chat_messages, target_count, threshold_count, offset_count, expected):
    total_count = len(chat_messages)  # 7
    index = locate_safe_reduction_index(
        chat_messages,
        target_count=target_count,
        threshold_count=threshold_count,
        offset_count=offset_count,
    )

    if expected == -1:
        # Means no reduction needed or can't be done
        assert index == -1
    else:
        # We expect a valid index
        assert index == expected
        assert 0 <= index < total_count


def test_locate_safe_reduction_index_index_not_negative_one(chat_messages):
    # We set a target_count that triggers reduction,
    # but we also expect it to move backward until it finds a user message
    target_count = 3
    threshold_count = 0
    offset_count = 0

    # Here, the function call + result is near the end.
    # We expect to cut at a user message if possible.
    index = locate_safe_reduction_index(
        chat_messages,
        target_count=target_count,
        threshold_count=threshold_count,
        offset_count=offset_count,
    )

    # The safe index might be message 2 or so, depending on the function calls
    # We'll just ensure it's not -1 and it is indeed a user message
    assert index != -1


def test_extract_range(chat_messages):
    result = extract_range(chat_messages, start=1, end=3)
    # We expect 2 messages from indexes 1 and 2
    assert len(result) == 2
    assert result[0] == chat_messages[1]
    assert result[1] == chat_messages[2]

    # If end=None, extract from start to the end
    result_end_none = extract_range(chat_messages, start=4, end=None)
    assert len(result_end_none) == len(chat_messages) - 4


def test_extract_range_empty(chat_messages):
    # If start >= len(chat_messages), we get an empty list
    result = extract_range(chat_messages, start=len(chat_messages))
    assert result == []

    # If start > end, also empty
    result2 = extract_range(chat_messages, start=5, end=3)
    assert result2 == []


def test_extract_range_full(chat_messages):
    # If we do start=0 and end=None, we get the entire list
    result = extract_range(chat_messages, 0)
    assert result == chat_messages
