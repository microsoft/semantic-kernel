# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import Callable

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.utils.author_role import AuthorRole

logger = logging.getLogger(__name__)


SUMMARY_METADATA_KEY = "__summary__"


def locate_summarization_boundary(history: list[ChatMessageContent]) -> int:
    """Identify the index of the first message that is not a summary message.

    This is indicated by the presence of the SUMMARY_METADATA_KEY in the message metadata.

    Returns:
        The insertion point index for normal history messages (i.e., after all summary messages).
    """
    for idx, msg in enumerate(history):
        if not msg.metadata or SUMMARY_METADATA_KEY not in msg.metadata:
            return idx
    return len(history)


def locate_safe_reduction_index(
    history: list[ChatMessageContent],
    target_count: int,
    threshold_count: int = 0,
    offset_count: int = 0,
) -> int | None:
    """Identify the index of the first message at or beyond the specified target_count.

    This index does not orphan sensitive content (function calls/results).

    This method ensures that the presence of a function-call always follows with its result,
    so the function-call and its function-result are never separated.

    In addition, it attempts to locate a user message within the threshold window so that
    context with the subsequent assistant response is preserved.

    Args:
        history: The entire chat history.
        target_count: The desired message count after reduction.
        threshold_count: The threshold beyond target_count required to trigger reduction.
                         If total messages <= (target_count + threshold_count), no reduction occurs.
        offset_count: Optional number of messages to skip at the start (e.g. existing summary messages).

    Returns:
        The index that identifies the starting point for a reduced history that does not orphan
        sensitive content. Returns None if reduction is not needed.
    """
    total_count = len(history)
    threshold_index = total_count - (threshold_count or 0) - target_count

    if threshold_index <= offset_count:
        # History is too short to truncate
        return None

    # Start from the end to find a good cut
    message_index = total_count - target_count

    # Move backward to avoid cutting through function call/results
    while message_index >= offset_count:
        # If this message is not a function call/result, we can break
        if not any(
            isinstance(item, (FunctionCallContent, FunctionResultContent)) for item in history[message_index].items
        ):
            break
        message_index -= 1

    # This is our initial target truncation index
    target_index = message_index

    # Attempt to see if there's a user message in the threshold window
    while message_index >= threshold_index:
        if history[message_index].role == AuthorRole.USER:
            return message_index
        message_index -= 1

    return target_index


def extract_range(
    history: list[ChatMessageContent],
    start: int,
    end: int | None = None,
    filter_func: Callable[[ChatMessageContent], bool] | None = None,
) -> list[ChatMessageContent]:
    """Extract a range of messages from the source history, skipping any message for which we do not want to keep.

    For example, function calls/results, if desired.

    Args:
        history: The source history.
        start: The index of the first message to extract (inclusive).
        end: The index of the last message to extract (exclusive). If None, extracts through end.
        filter_func: A function that takes a ChatMessageContent and returns True if the message should
                        be skipped, False otherwise.

    Returns:
        A list of extracted messages.
    """
    if end is None:
        end = len(history)
    sliced = history[start:end]
    if filter_func is None:
        return sliced
    return [m for m in sliced if not filter_func(m)]
