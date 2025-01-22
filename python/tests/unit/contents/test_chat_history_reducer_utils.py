# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.history_reducer.chat_history_reducer_utils import (
    SUMMARY_METADATA_KEY,
    contains_function_call_or_result,
    extract_range,
    get_call_result_pairs,
    locate_safe_reduction_index,
    locate_summarization_boundary,
)
from semantic_kernel.contents.utils.author_role import AuthorRole


@pytest.fixture
def chat_messages_with_pairs():
    msgs = []

    # 1) Summary message at index 0 (system)
    msg_summary = ChatMessageContent(role=AuthorRole.SYSTEM, content="Summary so far.")
    msg_summary.metadata[SUMMARY_METADATA_KEY] = True
    msgs.append(msg_summary)

    # 2) Normal user message
    msgs.append(ChatMessageContent(role=AuthorRole.USER, content="User says hello."))

    # 3) Function call (call ID = "call1")
    msg_func_call_1 = ChatMessageContent(role=AuthorRole.ASSISTANT, content="Function call #1")
    func_call_content_1 = FunctionCallContent(id="call1", function_name="funcA", arguments={"param": "valA"})
    msg_func_call_1.items.append(func_call_content_1)
    msgs.append(msg_func_call_1)

    # 4) Function result for call1
    msg_func_result_1 = ChatMessageContent(role=AuthorRole.ASSISTANT, content="Result for call #1")
    func_result_content_1 = FunctionResultContent(id="call1", content="Function #1 result text")
    msg_func_result_1.items.append(func_result_content_1)
    msgs.append(msg_func_result_1)

    # 5) Another user message
    msgs.append(ChatMessageContent(role=AuthorRole.USER, content="Another user message."))

    # 6) Another function call (call ID = "call2")
    msg_func_call_2 = ChatMessageContent(role=AuthorRole.ASSISTANT, content="Function call #2")
    func_call_content_2 = FunctionCallContent(id="call2", function_name="funcB", arguments={"param": "valB"})
    msg_func_call_2.items.append(func_call_content_2)
    msgs.append(msg_func_call_2)

    # 7) Another user message (no result yet for "call2")
    msgs.append(ChatMessageContent(role=AuthorRole.USER, content="Wait, function result not yet?"))

    # 8) Unrelated function result (call ID = "callX" doesn't match any prior call)
    msg_func_result_x = ChatMessageContent(role=AuthorRole.ASSISTANT, content="Result for unknown call")
    func_result_content_x = FunctionResultContent(id="callX", content="No matching call.")
    msg_func_result_x.items.append(func_result_content_x)
    msgs.append(msg_func_result_x)

    # 9) Function result for call2
    msg_func_result_2 = ChatMessageContent(role=AuthorRole.ASSISTANT, content="Result for call #2")
    func_result_content_2 = FunctionResultContent(id="call2", content="Function #2 result text")
    msg_func_result_2.items.append(func_result_content_2)
    msgs.append(msg_func_result_2)

    return msgs


def test_get_call_result_pairs_fixture_has_pairs(chat_messages_with_pairs):
    """
    Since 'chat_messages_with_pairs' includes function calls with IDs,
    we expect pairs. Specifically:
      - (2,3) for call1
      - (5,8) for call2
    """
    pairs = get_call_result_pairs(chat_messages_with_pairs)
    assert (2, 3) in pairs, "Expected pair for (call1) in indexes (2,3)."
    assert (5, 8) in pairs, "Expected pair for (call2) in indexes (5,8)."
    assert len(pairs) == 2, "Fixture should produce exactly two matched call->result pairs."


@pytest.mark.parametrize(
    "message_items,expected",
    [
        ([], False),
        ([FunctionCallContent(function_name="funcA", arguments={})], True),
        ([FunctionResultContent(id="test", content="Result")], True),
    ],
)
def test_contains_function_call_or_result(message_items, expected):
    msg = ChatMessageContent(role=AuthorRole.USER, content="Test")
    msg.items.extend(message_items)
    assert contains_function_call_or_result(msg) == expected


def test_extract_range_preserve_pairs(chat_messages_with_pairs):
    """
    Tests that extract_range with preserve_pairs=True keeps or skips
    call/result pairs together. We'll slice from index=2 to index=9
    in the updated fixture.
    """
    extracted = extract_range(
        chat_messages_with_pairs,
        start=2,
        end=9,  # exclusive of index=9
        preserve_pairs=True,
    )

    # Indices in range(2..9) => 2,3,4,5,6,7,8
    # The code should preserve both pairs if they're fully in the slice.
    # Pairs are (2,3) and (5,8). They are indeed fully inside [2..9).
    # So we expect to keep them plus indices 4,6,7. That totals 7 messages.
    assert len(extracted) == 7

    # Instead of asserting exact positional equality, just check we
    # have the same set of messages from 2..9 (no duplicates or omissions).
    expected_slice = chat_messages_with_pairs[2:9]  # indexes 2..8
    assert set(extracted) == set(expected_slice), "Expected messages 2..8 to be returned."


def test_extract_range_preserve_pairs_call_outside_slice(chat_messages_with_pairs):
    """
    If a function call is outside the start/end range but the result is inside,
    we do NOT have to preserve that pair since it's partially out of range.
    We'll pick start=4, end=9 => indices 4..8.
    """
    extracted = extract_range(chat_messages_with_pairs, start=4, end=9, preserve_pairs=True)

    # Indices in range(4..9) => 4,5,6,7,8
    # Pairs: (2,3) is outside, (5,8) is fully inside. So (5,8) is kept together.
    # The final set of messages is [4,5,6,7,8] => 5 total.
    assert len(extracted) == 5

    expected_slice = chat_messages_with_pairs[4:9]  # indexes 4..8
    assert set(extracted) == set(expected_slice), "Expected messages 4..8 to be returned."

    # (2,3) do not appear, and that's correct since they're outside this slice.


def test_locate_summarization_boundary_empty():
    # Edge case: empty history => boundary = 0
    empty_history = []
    assert locate_summarization_boundary(empty_history) == 0


def test_locate_safe_reduction_index_multiple_calls(chat_messages_with_pairs):
    """
    If we set a small target_count, the code will attempt to find a safe
    reduction index that doesn't orphan a function call/result pair.
    """
    total_count = len(chat_messages_with_pairs)  # 9
    target_count = 4
    idx = locate_safe_reduction_index(
        chat_messages_with_pairs,
        target_count=target_count,
        threshold_count=0,
        offset_count=0,
    )
    # We expect a valid index because total_count (9) > target_count (4).
    assert idx is not None and 0 < idx < total_count

    # Verify that from idx onward, we haven't split a matched call->result pair.
    pairs = get_call_result_pairs(chat_messages_with_pairs)
    for call_i, result_i in pairs:
        if call_i >= idx:
            # If the call is in the reduced set, the result must be in the reduced set:
            assert result_i >= idx
        if result_i >= idx:
            # If the result is in the reduced set, the call must be in the reduced set:
            assert call_i >= idx


def test_locate_safe_reduction_index_high_offset(chat_messages_with_pairs):
    """
    If offset_count is large, we might not be able to reduce. Then the function
    can return None if no valid reduction can be found after skipping the offset.
    """
    target_count = 3
    threshold_count = 0
    offset_count = 5

    idx = locate_safe_reduction_index(
        chat_messages_with_pairs,
        target_count=target_count,
        threshold_count=threshold_count,
        offset_count=offset_count,
    )

    # Possibly None if we cannot reduce after skipping the first 5 messages.
    if idx is not None:
        # Then it must be >= offset_count
        assert idx >= offset_count
    else:
        # It's fine if it returns None, meaning no valid safe reduction was found.
        pass
