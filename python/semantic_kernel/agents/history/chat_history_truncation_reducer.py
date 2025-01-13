import logging

from semantic_kernel.agents.history.chat_history_reducer import ChatHistoryReducer
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.kernel_pydantic import KernelBaseModel

logger = logging.getLogger(__name__)


class ChatHistoryTruncationReducer(KernelBaseModel, ChatHistoryReducer):
    """Truncate the chat history to the target message count.

    Avoids orphaning user messages or function-calls/results within a threshold window.
    """

    target_count: int
    threshold_count: int | None = 0

    def __init__(self, target_count: int, threshold_count: int | None = None, **data):
        super().__init__(target_count=target_count, threshold_count=threshold_count or 0, **data)
        if self.target_count <= 0:
            raise ValueError("Target message count must be greater than zero.")
        if self.threshold_count < 0:
            raise ValueError("The threshold_count must be nonnegative.")

    async def reduce(self, history: list[ChatMessageContent]) -> list[ChatMessageContent] | None:
        """Reduce the chat history to the target message count."""
        if len(history) <= self.target_count + (self.threshold_count or 0):
            # No need to reduce
            return None

        # 1. Figure out the safe index to start from, so we don't orphan function calls or the most recent user message.
        logger.debug("Performing chat history truncation check...")

        truncation_index = locate_safe_reduction_index(history, self.target_count, self.threshold_count)
        if truncation_index <= 0:
            # No valid truncation point found
            return None

        # 2. Actually truncate the history
        truncated_history = extract_range(history, start_index=truncation_index)
        return truncated_history


def locate_safe_reduction_index(
    history: list[ChatMessageContent], target_count: int, threshold_count: int | None = None
) -> int:
    """Identify the first message at or beyond the specified target_count.

    This will not orphan sensitive content (function calls/results).
    Also tries to keep a user->assistant pairing within threshold_count range.
    Returns -1 if no valid index is found.
    """
    threshold_count = threshold_count or 0
    # The earliest point at which we can consider truncation:
    # e.g., we allow target_count plus the threshold_count beyond it.
    # If the history is shorter than that, no reduction needed.
    threshold_index = len(history) - (target_count + threshold_count)
    if threshold_index <= 0:
        return -1

    # The actual "ideal" truncation index is len(history) - target_count
    message_index = len(history) - target_count
    if message_index < 0:
        return -1

    # Skip function-call related messages backward
    while message_index > 0 and is_function_related(history[message_index]):
        message_index -= 1

    if message_index < threshold_index:
        # We tried to shift to avoid function calls, but ended up outside threshold
        # fallback is to use the earliest (threshold_index).
        message_index = threshold_index

    return message_index


def is_function_related(msg: ChatMessageContent) -> bool:
    """In .NET, we test for function calls or function results.

    Adjust this logic as needed for your usage.
    """
    return any(item.__class__.__name__ in ("FunctionCallContent", "FunctionResultContent") for item in msg.items)


def extract_range(
    history: list[ChatMessageContent],
    start_index: int,
    end_index: int | None = None,
) -> list[ChatMessageContent]:
    """Extract messages from start_index to end_index (inclusive).

    If end_index is not specified, use the remainder of the list.
    """
    if start_index < 0:
        start_index = 0
    if end_index is None or end_index > len(history):
        end_index = len(history)
    return history[start_index:end_index]
