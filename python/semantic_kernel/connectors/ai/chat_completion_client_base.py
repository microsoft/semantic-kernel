# Copyright (c) Microsoft. All rights reserved.

# from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, AsyncGenerator, Dict, List

from semantic_kernel.connectors.ai.ai_service_client_base import AIServiceClientBase
from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings

if TYPE_CHECKING:
    from semantic_kernel.models.chat.chat_completion_result import (
        ChatCompletionResult,
    )


class ChatCompletionClientBase(AIServiceClientBase):
    """Base class for all Chat Completion Services"""

    # @abstractmethod
    async def complete_chat_async(
        self,
        messages: List[Dict[str, str]],
        settings: "ChatRequestSettings",
    ) -> "ChatCompletionResult":
        """
        This is the method that is called from the kernel to get a response from a chat-optimized LLM.

        Arguments:
            messages {List[Dict[str, str]]} -- A list of tuples, where each tuple is
                comprised of a speaker ID and a message.
            settings {ChatRequestSettings} -- Settings for the request.

        Returns:
            ChatCompletionResult -- A object with all the results from the LLM.
        """
        raise NotImplementedError(
            "complete_chat_async has to be implemented by the used subclass."
        )

    # @abstractmethod
    async def complete_chat_stream_async(
        self,
        messages: List[Dict[str, str]],
        settings: "ChatRequestSettings",
    ) -> AsyncGenerator["ChatCompletionResult", None]:
        """
        This is the method that is called from the kernel to get a stream response from a chat-optimized LLM.

        Arguments:
            messages {List[Dict[str, str]]} -- A list of tuples, where each tuple is
                comprised of a speaker ID and a message.
            settings {ChatRequestSettings} -- Settings for the request.

        Yields:
            A stream representing LLM completion results.
        """
        raise NotImplementedError(
            "complete_chat_stream_async has to be implemented by the used subclass."
        )
