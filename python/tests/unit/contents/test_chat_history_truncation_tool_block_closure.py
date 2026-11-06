# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.history_reducer.chat_history_reducer_utils import locate_safe_reduction_index
from semantic_kernel.contents.history_reducer.chat_history_truncation_reducer import ChatHistoryTruncationReducer
from semantic_kernel.contents.utils.author_role import AuthorRole


def _call(cid: str) -> ChatMessageContent:
    m = ChatMessageContent(role=AuthorRole.ASSISTANT, content="")
    m.items.append(FunctionCallContent(id=cid, function_name=f"f{cid}", plugin_name="p", arguments={}))
    return m


def _has_call(history: list[ChatMessageContent], cid: str) -> bool:
    return any(isinstance(item, FunctionCallContent) and item.id == cid for msg in history for item in msg.items)


def _has_result(history: list[ChatMessageContent], cid: str) -> bool:
    return any(isinstance(item, FunctionResultContent) and item.id == cid for msg in history for item in msg.items)


async def test_public_reducer_keeps_text_tool_without_orphaning_earlier_call():
    """Copilot r4415468227 case through the public reducer API.

    [user, call A, call B, TOOL(text result A), assistant, TOOL(result B)]
    target_count=2. On base the cut lands at idx=2, dropping call A but keeping
    the TOOL message carrying text for A. After the fix the cut moves to idx=1
    so both call A and its text-result TOOL are retained.
    """
    history = [
        ChatMessageContent(role=AuthorRole.USER, content="u0"),
        _call("A"),
        _call("B"),
        ChatMessageContent(role=AuthorRole.TOOL, content="result A as plain text"),
        ChatMessageContent(role=AuthorRole.ASSISTANT, content="text"),
        ChatMessageContent(
            role=AuthorRole.TOOL,
            items=[FunctionResultContent(id="B", function_name="fB", plugin_name="p", result="r-B")],
        ),
    ]
    reducer = ChatHistoryTruncationReducer(target_count=2, threshold_count=0)
    reducer.messages = history
    result = await reducer.reduce()

    assert result is not None
    kept = result.messages
    assert _has_call(kept, "B"), "call B should be retained"
    assert _has_result(kept, "B"), "result B should be retained"
    assert _has_call(kept, "A"), "call A must be retained alongside its text TOOL result"
    assert any(msg.role == AuthorRole.TOOL and msg.content == "result A as plain text" for msg in kept), (
        "the text-only TOOL result for A must be retained alongside call A"
    )


def test_chained_closure_requires_multiple_adjacency_id_rounds():
    """n=10 history with two ID pairs and a text-only TOOL block.

    Initial cut at 8. ID closure for (B,resultB) moves to 5; ID closure for
    (A,resultA) moves to 2; adjacency re-walk from 2 moves to 1 (call X).
    On base (no adjacency re-walk) the cut stops at 2, orphaning the text-only
    TOOL for X at msg3.
    """
    history = [
        ChatMessageContent(role=AuthorRole.USER, content="u0"),  # 0
        _call("X"),  # 1
        _call("A"),  # 2
        ChatMessageContent(role=AuthorRole.TOOL, content="text X"),  # 3 (no FunctionResult)
        ChatMessageContent(role=AuthorRole.ASSISTANT, content="text"),  # 4
        _call("B"),  # 5
        ChatMessageContent(
            role=AuthorRole.TOOL,
            items=[FunctionResultContent(id="A", function_name="fA", plugin_name="p", result="r-A")],
        ),  # 6
        ChatMessageContent(role=AuthorRole.TOOL, content="text B"),  # 7 (no FunctionResult)
        ChatMessageContent(role=AuthorRole.ASSISTANT, content="text"),  # 8
        ChatMessageContent(
            role=AuthorRole.TOOL,
            items=[FunctionResultContent(id="B", function_name="fB", plugin_name="p", result="r-B")],
        ),  # 9
    ]
    idx = locate_safe_reduction_index(history, target_count=2, threshold_count=0)
    assert idx is not None
    assert idx == 1, f"expected cut at call X (idx=1), got {idx}"
