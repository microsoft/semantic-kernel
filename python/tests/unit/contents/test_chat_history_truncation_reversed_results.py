# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.history_reducer.chat_history_truncation_reducer import ChatHistoryTruncationReducer
from semantic_kernel.contents.utils.author_role import AuthorRole


def _assistant_call(call_id: str) -> ChatMessageContent:
    m = ChatMessageContent(role=AuthorRole.ASSISTANT, content="")
    m.items.append(FunctionCallContent(id=call_id, function_name="f", plugin_name="p", arguments={}))
    return m


def _tool_message_with(results: list[str]) -> ChatMessageContent:
    m = ChatMessageContent(role=AuthorRole.TOOL, content="")
    for rid in results:
        m.items.append(FunctionResultContent(id=rid, function_name="f", plugin_name="p", result=f"r-{rid}"))
    return m


def _has_call(history: list[ChatMessageContent], call_id: str) -> bool:
    return any(
        isinstance(item, FunctionCallContent) and item.id == call_id for message in history for item in message.items
    )


def _has_result(history: list[ChatMessageContent], call_id: str) -> bool:
    return any(
        isinstance(item, FunctionResultContent) and item.id == call_id for message in history for item in message.items
    )


async def test_truncation_does_not_orphan_earlier_call_when_results_reversed_in_one_message():
    # c2 call is at msg1 (earlier). c3 call is at msg3 (later).
    # Both results are in ONE tool message (msg4), but ordered [result_c3, result_c2]
    # (later call first). The break bug skipped result_c2 in pair matching, leaving
    # c2's result orphaned when the cut removes msg1 but keeps msg4.
    history = [
        ChatMessageContent(role=AuthorRole.USER, content="u0"),
        _assistant_call("c2"),
        ChatMessageContent(role=AuthorRole.USER, content="u1"),
        _assistant_call("c3"),
        _tool_message_with(["c3", "c2"]),  # reversed: later call result first
        ChatMessageContent(role=AuthorRole.ASSISTANT, content="text"),
    ]

    reducer = ChatHistoryTruncationReducer(target_count=3, threshold_count=0)
    reducer.messages = history
    result = await reducer.reduce()

    assert result is not None
    # If c3's result is kept, c3's call must be kept.
    if _has_result(result.messages, "c3"):
        assert _has_call(result.messages, "c3"), "c3 result kept without c3 call"
    # Critical: if c2's result is kept (it is in the same msg as c3's result),
    # c2's call must also be kept. Without the fix, c2 is orphaned.
    if _has_result(result.messages, "c2"):
        assert _has_call(result.messages, "c2"), "c2 result kept without c2 call (orphan)"
