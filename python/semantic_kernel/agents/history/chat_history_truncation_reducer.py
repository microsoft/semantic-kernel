# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Any

from pydantic import Field

from semantic_kernel.agents.history.chat_history_reducer import ChatHistoryReducer
from semantic_kernel.agents.history.chat_history_reducer_extensions import extract_range, locate_safe_reduction_index
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.kernel_pydantic import KernelBaseModel

logger = logging.getLogger(__name__)


class ChatHistoryTruncationReducer(KernelBaseModel, ChatHistoryReducer):
    """Truncate the chat history to the target message count.

    Avoids orphaning user messages or function-calls/results within a threshold window.
    """

    target_count: int = Field(..., gt=0, description="The target message count to reduce the chat history to.")
    threshold_count: int = Field(default=0, ge=0, description="The threshold count to avoid orphaning messages.")

    def __init__(self, target_count: int, threshold_count: int | None = None):
        """Initialize the truncation reducer."""
        args: dict[str, Any] = {
            "target_count": target_count,
        }

        if threshold_count is not None:
            args["threshold_count"] = threshold_count

        super().__init__(**args)

    def __eq__(self, other: object) -> bool:
        """Return whether this instance is equal to another."""
        if not isinstance(other, ChatHistoryTruncationReducer):
            return False
        return self.threshold_count == other.threshold_count and self.target_count == other.target_count

    def __hash__(self) -> int:
        """Return a hash code for this instance."""
        return hash((self.__class__.__name__, self.threshold_count, self.target_count))

    async def reduce(self, history: list[ChatMessageContent]) -> list[ChatMessageContent] | None:
        """Reduce the chat history to the target message count."""
        if len(history) <= self.target_count + (self.threshold_count or 0):
            # No need to reduce
            return None

        logger.info("Performing chat history truncation check...")

        truncation_index = locate_safe_reduction_index(history, self.target_count, self.threshold_count)
        if truncation_index < 0:
            logger.info(
                f"No truncation index found. Target count: {self.target_count}, Threshold count: {self.threshold_count}"
            )
            return None

        logger.info(f"Valid truncation index found. Truncating history to {truncation_index} messages.")

        return extract_range(history, start=truncation_index)
