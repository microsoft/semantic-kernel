# Copyright (c) Microsoft. All rights reserved.

import sys
from abc import ABC, abstractmethod
from typing import Any

if sys.version < "3.11":
    from typing_extensions import Self  # pragma: no cover
else:
    from typing import Self  # type: ignore # pragma: no cover

from pydantic import Field

from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.exceptions.content_exceptions import ContentInitializationError
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class ChatHistoryReducer(ChatHistory, ABC):
    """Defines a contract for reducing chat history."""

    target_count: int = Field(..., gt=0, description="Target message count.")
    threshold_count: int = Field(default=0, ge=0, description="Threshold count to avoid orphaning messages.")
    auto_reduce: bool = Field(
        default=False,
        description="Whether to automatically reduce the chat history, this happens when using add_message_async.",
    )

    @abstractmethod
    async def reduce(self) -> Self | None:
        """Reduce the chat history in some way (e.g., truncate, summarize).

        Returns:
            A possibly shorter list of messages, or None if no change is needed.
        """
        ...

    async def add_message_async(
        self,
        message: ChatMessageContent | dict[str, Any],
        encoding: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a message to the chat history.

        If auto_reduce is enabled, the history will be reduced after adding the message.
        """
        if isinstance(message, ChatMessageContent):
            self.messages.append(message)
            if self.auto_reduce:
                await self.reduce()
            return
        if "role" not in message:
            raise ContentInitializationError(f"Dictionary must contain at least the role. Got: {message}")
        if encoding:
            message["encoding"] = encoding
        if metadata:
            message["metadata"] = metadata
        self.messages.append(ChatMessageContent(**message))
        if self.auto_reduce:
            await self.reduce()
