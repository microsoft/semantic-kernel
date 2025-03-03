# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import Callable

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.utils.feature_stage_decorator import experimental

logger = logging.getLogger(__name__)


SUMMARY_METADATA_KEY = "__summary__"


@experimental
def get_call_result_pairs(history: list[ChatMessageContent]) -> list[tuple[int, int]]:
    """Identify all (FunctionCallContent, FunctionResultContent) pairs in the history.

    Return a list of (call_index, result_index) pairs for safe referencing.
    """
    pairs: list[tuple[int, int]] = []  # Correct type: list of tuples with integers
    call_ids_seen: dict[str, int] = {}  # Map call IDs (str) to their indices (int)

    # Gather all function-call IDs and their indices.
    for i, msg in enumerate(history):
        for item in msg.items:
            if isinstance(item, FunctionCallContent) and item.id is not None:
                call_ids_seen[item.id] = i

    # Now, match each FunctionResultContent to the earliest call ID with the same ID.
    for j, msg in enumerate(history):
        for item in msg.items:
            if isinstance(item, FunctionResultContent) and item.id is not None:
                call_id = item.id
                if call_id in call_ids_seen:
                    call_index = call_ids_seen[call_id]
                    pairs.append((call_index, j))
                    # Remove the call ID so we don't match it a second time
                    del call_ids_seen[call_id]
                    break

    return pairs


@experimental
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


@experimental
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
        return None

    message_index = total_count - target_count

    # Move backward to avoid cutting function calls / results
    # also skip over developer/system messages
    while message_index >= offset_count:
        if history[message_index].role not in (AuthorRole.DEVELOPER, AuthorRole.SYSTEM):
            break
        if not contains_function_call_or_result(history[message_index]):
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


@experimental
def extract_range(
    history: list[ChatMessageContent],
    start: int,
    end: int | None = None,
    filter_func: Callable[[ChatMessageContent], bool] | None = None,
    preserve_pairs: bool = False,
) -> list[ChatMessageContent]:
    """Extract a range of messages from the source history, skipping any message for which we do not want to keep.

    For example, function calls/results, if desired.

    Args:
        history: The source history.
        start: The index of the first message to extract (inclusive).
        end: The index of the last message to extract (exclusive). If None, extracts through end.
        filter_func: A function that takes a ChatMessageContent and returns True if the message should
                        be skipped, False otherwise.
        preserve_pairs: If True, ensures that function call and result pairs are either both kept or both skipped.

    Returns:
        A list of extracted messages.
    """
    if end is None:
        end = len(history)

    sliced = list(range(start, end))

    # If we need to preserve call->result pairs, gather them
    pair_map = {}
    if preserve_pairs:
        pairs = get_call_result_pairs(history)
        # store in a dict for quick membership checking
        # call_idx -> result_idx, and also result_idx -> call_idx
        for cidx, ridx in pairs:
            pair_map[cidx] = ridx
            pair_map[ridx] = cidx

    extracted: list[ChatMessageContent] = []
    i = 0
    while i < len(sliced):
        idx = sliced[i]
        msg = history[idx]

        # If filter_func excludes it, skip it
        if filter_func and filter_func(msg):
            i += 1
            continue

        # skipping system/developer message
        if msg.role in (AuthorRole.DEVELOPER, AuthorRole.SYSTEM):
            i += 1
            continue

        # If preserve_pairs is on, and there's a paired index, skip or include them both
        if preserve_pairs and idx in pair_map:
            paired_idx = pair_map[idx]
            # If the pair is within [start, end), we must keep or skip them together
            if start <= paired_idx < end:
                # Check if the pair or itself fails filter_func
                if filter_func and (filter_func(history[paired_idx]) or filter_func(msg)):
                    # skip both
                    i += 1
                    # Also skip the paired index if it's in our current slice
                    if paired_idx in sliced:
                        # remove it from the slice so we don't process it again
                        sliced.remove(paired_idx)
                    continue
                # keep both
                extracted.append(msg)
                if paired_idx > idx:
                    # We'll skip the pair in the normal iteration by removing from slice
                    # but add it to extracted right now
                    extracted.append(history[paired_idx])
                    if paired_idx in sliced:
                        sliced.remove(paired_idx)
                else:
                    # if paired_idx < idx, it might appear later, so skip for now
                    # but we may have already processed it if i was the 2nd item
                    # either way, do not add duplicates
                    pass
                i += 1
                continue
            # If the paired_idx is outside [start, end), there's no conflict
            # so we can just do normal logic
            extracted.append(msg)
            i += 1
        else:
            # keep it if filter_func not triggered
            extracted.append(msg)
            i += 1

    return extracted


@experimental
def contains_function_call_or_result(msg: ChatMessageContent) -> bool:
    """Return True if the message has any function call or function result."""
    return any(isinstance(item, (FunctionCallContent, FunctionResultContent)) for item in msg.items)
