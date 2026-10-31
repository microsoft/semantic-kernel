# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.history_reducer.chat_history_reducer_utils import get_call_result_pairs
from semantic_kernel.contents.utils.author_role import AuthorRole


def _assistant_with(calls):
    m = ChatMessageContent(role=AuthorRole.ASSISTANT, content="")
    for cid in calls:
        m.items.append(FunctionCallContent(id=cid, function_name="f", plugin_name="p", arguments={}))
    return m


def _tool_with(results):
    m = ChatMessageContent(role=AuthorRole.TOOL, content="")
    for rid in results:
        m.items.append(FunctionResultContent(id=rid, function_name="f", plugin_name="p", result="r"))
    return m


def test_multiple_results_in_one_tool_message_are_all_paired():
    history = [
        ChatMessageContent(role=AuthorRole.USER, content="u1"),
        _assistant_with(["c1"]),
        _tool_with(["c1"]),
        ChatMessageContent(role=AuthorRole.USER, content="u2"),
        _assistant_with(["c2", "c3"]),
        _tool_with(["c2", "c3"]),
    ]
    pairs = get_call_result_pairs(history)
    call_indices = [c for c, r in pairs]
    assert 4 in call_indices, f"Expected call at msg4 in pairs, got {pairs}"
    assert call_indices.count(4) == 2, f"Expected two pairs for msg4 (c2,c3), got {pairs}"


def test_multiple_results_across_separate_messages():
    history = [
        ChatMessageContent(role=AuthorRole.USER, content="u1"),
        _assistant_with(["c1", "c2"]),
        ChatMessageContent(role=AuthorRole.ASSISTANT, content="text"),
        _tool_with(["c1"]),
        _tool_with(["c2"]),
    ]
    pairs = get_call_result_pairs(history)
    assert (1, 3) in pairs, f"Expected (1,3), got {pairs}"
    assert (1, 4) in pairs, f"Expected (1,4), got {pairs}"
