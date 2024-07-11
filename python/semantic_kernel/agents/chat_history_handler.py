# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from collections.abc import AsyncIterable
from typing import TYPE_CHECKING

from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.contents.chat_history import ChatHistory
    from semantic_kernel.contents.chat_message_content import ChatMessageContent
    from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent


@experimental_class
class ChatHistoryHandler(ABC):
    """Contract for an agent that utilizes a ChatHistoryChannel."""

    @abstractmethod
    async def invoke(self, history: "ChatHistory") -> AsyncIterable["ChatMessageContent"]:
        """Invoke the chat history handler.

        Entry point for calling into an agent from a ChatHistoryChannel
        """
        ...

    @abstractmethod
    async def invoke_stream(self, history: "ChatHistory") -> AsyncIterable["StreamingChatMessageContent"]:
        """Invoke the chat history handler in streaming mode.

        Entry point for calling into an agent from a ChatHistoryChannel for streaming content.
        """
        ...
