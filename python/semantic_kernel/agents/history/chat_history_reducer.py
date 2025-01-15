# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from semantic_kernel.contents.chat_message_content import ChatMessageContent


class ChatHistoryReducer(ABC):
    """Defines a contract for reducing chat history."""

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        """Return whether this instance is equal to another."""
        raise NotImplementedError

    @abstractmethod
    def __hash__(self) -> int:
        """Return a hash code for this instance."""
        raise NotImplementedError

    @abstractmethod
    async def reduce(self, history: list["ChatMessageContent"]) -> list["ChatMessageContent"] | None:
        """Reduce the chat history to a target message count."""
        ...
