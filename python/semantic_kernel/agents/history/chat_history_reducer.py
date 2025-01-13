# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from semantic_kernel.contents.chat_message_content import ChatMessageContent


class ChatHistoryReducer(Protocol):
    """Defines a contract for reducing chat history."""

    async def reduce(self, history: list["ChatMessageContent"]) -> list["ChatMessageContent"] | None:
        """Reduce the chat history to a target message count."""
        ...
