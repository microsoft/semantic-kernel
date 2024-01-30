# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, AsyncIterable, List, Optional

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
    from semantic_kernel.models.chat.chat_message import ChatMessage
    from semantic_kernel.models.contents import ChatMessageContent, StreamingChatMessageContent


class ChatCompletionClientBase(ABC):
    @abstractmethod
    async def complete_chat(
        self,
        messages: List["ChatMessage"],
        settings: "AIRequestSettings",
        logger: Optional[Any] = None,
    ) -> List["ChatMessageContent"]:
        """
        This is the method that is called from the kernel to get a response from a chat-optimized LLM.

        Arguments:
            messages {List[ChatMessage]} -- A list of chat messages, that can be rendered into a
                set of messages, from system, user, assistant and function.
            settings {AIRequestSettings} -- Settings for the request.
            logger {Logger} -- A logger to use for logging. (Deprecated)

        Returns:
            Union[str, List[str]] -- A string or list of strings representing the response(s) from the LLM.
        """
        pass

    @abstractmethod
    async def complete_chat_stream(
        self,
        messages: List["ChatMessage"],
        settings: "AIRequestSettings",
        logger: Optional[Any] = None,
    ) -> AsyncIterable[List["StreamingChatMessageContent"]]:
        """
        This is the method that is called from the kernel to get a stream response from a chat-optimized LLM.

        Arguments:
            messages {List[ChatMessage]} -- A list of chat messages, that can be rendered into a
                set of messages, from system, user, assistant and function.
            settings {AIRequestSettings} -- Settings for the request.
            logger {Logger} -- A logger to use for logging. (Deprecated)

        Yields:
            A stream representing the response(s) from the LLM.
        """
        pass
