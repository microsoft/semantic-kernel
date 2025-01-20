# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pydantic import Field

from semantic_kernel.contents.chat_history import ChatHistory

if TYPE_CHECKING:
    from semantic_kernel.contents.chat_message_content import ChatMessageContent


class ChatHistoryReducer(ChatHistory, ABC):
    """Defines a contract for reducing chat history."""

    target_count: int = Field(..., gt=0, description="Target message count.")
    threshold_count: int = Field(0, ge=0, description="Threshold count to avoid orphaning messages.")

    @abstractmethod
    async def reduce(self) -> list["ChatMessageContent"] | None:
        """Reduce the chat history in some way (e.g., truncate, summarize).

        Returns:
            A possibly shorter list of messages, or None if no change is needed.
        """
        ...
