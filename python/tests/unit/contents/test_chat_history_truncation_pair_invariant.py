# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.history_reducer.chat_history_reducer_utils import locate_safe_reduction_index
from semantic_kernel.contents.history_reducer.chat_history_truncation_reducer import ChatHistoryTruncationReducer
from semantic_kernel.contents.utils.author_role import AuthorRole


def _assistant_call(call_id: str, function_name: str = "search") -> ChatMessageContent:
    message = ChatMessageContent(role=AuthorRole.ASSISTANT, content="")
    message.items.append(
        FunctionCallContent(id=call_id, function_name=function_name, plugin_name="plugin", arguments={"q": call_id})
    )
    return message


def _tool_result(call_id: str, function_name: str = "search") -> ChatMessageContent:
    message = ChatMessageContent(role=AuthorRole.TOOL, content="")
    message.items.append(
        FunctionResultContent(id=call_id, function_name=function_name, plugin_name="plugin", result=f"result-{call_id}")
    )
    return message


def _has_call(history: list[ChatMessageContent], call_id: str) -> bool:
    return any(
        isinstance(item, FunctionCallContent) and item.id == call_id for message in history for item in message.items
    )


def _has_result(history: list[ChatMessageContent], call_id: str) -> bool:
    return any(
        isinstance(item, FunctionResultContent) and item.id == call_id for message in history for item in message.items
    )


async def test_truncation_keeps_nonadjacent_function_call_with_its_result():
    history = [
        ChatMessageContent(role=AuthorRole.USER, content="User message 1"),
        _assistant_call("call-1"),
        _tool_result("call-1"),
        ChatMessageContent(role=AuthorRole.USER, content="User message 2"),
        ChatMessageContent(role=AuthorRole.ASSISTANT, content="Assistant text between tool rounds."),
        _assistant_call("call-2"),
        ChatMessageContent(role=AuthorRole.ASSISTANT, content="Assistant text after tool call."),
        _tool_result("call-2"),
    ]

    assert history[1].role == AuthorRole.ASSISTANT
    assert history[2].role == AuthorRole.TOOL
    assert history[5].role == AuthorRole.ASSISTANT
    assert history[7].role == AuthorRole.TOOL

    reducer = ChatHistoryTruncationReducer(target_count=2, threshold_count=0)
    reducer.messages = history
    result = await reducer.reduce()

    assert result is not None
    assert _has_result(result.messages, "call-2")
    assert _has_call(result.messages, "call-2"), "A function result was retained without its matching function call."


async def test_truncation_keeps_adjacent_function_call_result_pair():
    history = [
        ChatMessageContent(role=AuthorRole.USER, content="User message 1"),
        _assistant_call("call-1"),
        _tool_result("call-1"),
        ChatMessageContent(role=AuthorRole.USER, content="User message 2"),
        _assistant_call("call-2"),
        _tool_result("call-2"),
    ]

    reducer = ChatHistoryTruncationReducer(target_count=2, threshold_count=0)
    reducer.messages = history
    result = await reducer.reduce()

    assert result is not None
    assert _has_call(result.messages, "call-2")
    assert _has_result(result.messages, "call-2")


async def test_truncation_keeps_multiple_calls_in_one_assistant_message():
    history = [
        ChatMessageContent(role=AuthorRole.USER, content="User message 1"),
        _assistant_call("call-1"),
        _tool_result("call-1"),
        ChatMessageContent(role=AuthorRole.USER, content="User message 2"),
        ChatMessageContent(role=AuthorRole.ASSISTANT, content=""),
        ChatMessageContent(role=AuthorRole.TOOL, content=""),
    ]
    assert history[4].role == AuthorRole.ASSISTANT
    assert history[5].role == AuthorRole.TOOL
    history[4].items.extend([
        FunctionCallContent(id="call-2", function_name="search", plugin_name="plugin", arguments={"q": "2"}),
        FunctionCallContent(id="call-3", function_name="lookup", plugin_name="plugin", arguments={"q": "3"}),
    ])
    history[5].items.extend([
        FunctionResultContent(id="call-2", function_name="search", plugin_name="plugin", result="result-2"),
        FunctionResultContent(id="call-3", function_name="lookup", plugin_name="plugin", result="result-3"),
    ])

    reducer = ChatHistoryTruncationReducer(target_count=2, threshold_count=0)
    reducer.messages = history
    result = await reducer.reduce()

    assert result is not None
    assert _has_call(result.messages, "call-2")
    assert _has_call(result.messages, "call-3")
    assert _has_result(result.messages, "call-2")
    assert _has_result(result.messages, "call-3")


async def test_truncation_does_not_reduce_when_threshold_window_does_not_trigger():
    history = [
        _assistant_call("call-a"),
        ChatMessageContent(role=AuthorRole.USER, content="User message"),
        _tool_result("call-a"),
    ]

    reducer = ChatHistoryTruncationReducer(target_count=2, threshold_count=2)
    reducer.messages = history
    result = await reducer.reduce()

    assert result is None


async def test_truncation_keeps_pair_when_threshold_window_selects_user_boundary():
    history = [
        ChatMessageContent(role=AuthorRole.USER, content="User message 0"),
        _assistant_call("call-a"),
        _tool_result("call-a"),
        _assistant_call("call-b"),
        ChatMessageContent(role=AuthorRole.USER, content="User message 1"),
        _tool_result("call-b"),
    ]

    reducer = ChatHistoryTruncationReducer(target_count=2, threshold_count=1)
    reducer.messages = history
    result = await reducer.reduce()

    assert result is not None
    assert _has_result(result.messages, "call-b")
    assert _has_call(result.messages, "call-b")


async def test_truncation_closure_keeps_chained_nonadjacent_pairs():
    history = [
        ChatMessageContent(role=AuthorRole.USER, content="User message 0"),
        _assistant_call("call-a"),
        ChatMessageContent(role=AuthorRole.ASSISTANT, content="Assistant between calls."),
        _assistant_call("call-b"),
        ChatMessageContent(role=AuthorRole.USER, content="User message 1"),
        _tool_result("call-b"),
        _tool_result("call-a"),
    ]

    reducer = ChatHistoryTruncationReducer(target_count=2, threshold_count=1)
    reducer.messages = history
    result = await reducer.reduce()

    assert result is not None
    assert _has_call(result.messages, "call-a")
    assert _has_result(result.messages, "call-a")
    assert _has_call(result.messages, "call-b")
    assert _has_result(result.messages, "call-b")


def test_locate_safe_reduction_index_rejects_pair_crossing_offset_boundary():
    history = [
        ChatMessageContent(role=AuthorRole.USER, content="User message 0"),
        _assistant_call("call-a"),
        ChatMessageContent(role=AuthorRole.USER, content="User message 1"),
        _tool_result("call-a"),
    ]

    assert (
        locate_safe_reduction_index(
            history=history,
            target_count=1,
            threshold_count=0,
            offset_count=2,
            has_system_message=False,
        )
        is None
    )


async def test_truncation_preserves_system_message_while_pairs_are_safe():
    reducer = ChatHistoryTruncationReducer(target_count=3, system_message="System prompt")
    reducer.add_message(ChatMessageContent(role=AuthorRole.USER, content="User message 1"))
    reducer.add_message(ChatMessageContent(role=AuthorRole.ASSISTANT, content="Assistant 1"))
    reducer.add_message(ChatMessageContent(role=AuthorRole.USER, content="User message 2"))
    reducer.add_message(ChatMessageContent(role=AuthorRole.ASSISTANT, content="Assistant 2"))

    result = await reducer.reduce()

    assert result is not None
    assert result.messages[0].role == AuthorRole.SYSTEM
    assert result.messages[0].content == "System prompt"
