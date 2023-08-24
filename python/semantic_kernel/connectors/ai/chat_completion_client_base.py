# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from logging import Logger
from typing import TYPE_CHECKING, List, Optional, Tuple, Union

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings


class ChatCompletionClientBase(ABC):
    @abstractmethod
    async def complete_chat_async(
        self,
        messages: List[Tuple[str, str]],
        settings: "ChatRequestSettings",
        logger: Optional[Logger] = None,
    ) -> Union[str, List[str]]:
        """
        This is the method that is called from the kernel to get a response from a chat-optimized LLM.

        Arguments:
            messages {List[Tuple[str, str]]} -- A list of tuples, where each tuple is
                comprised of a speaker ID and a message.
            settings {ChatRequestSettings} -- Settings for the request.
            logger {Logger} -- A logger to use for logging.

        Returns:
            Union[str, List[str]] -- A string or list of strings representing the response(s) from the LLM.
        """
        pass

    @abstractmethod
    async def complete_chat_stream_async(
        self,
        messages: List[Tuple[str, str]],
        settings: "ChatRequestSettings",
        logger: Optional[Logger] = None,
    ):
        """
        This is the method that is called from the kernel to get a stream response from a chat-optimized LLM.

        Arguments:
            messages {List[Tuple[str, str]]} -- A list of tuples, where each tuple is
                comprised of a speaker ID and a message.
            settings {ChatRequestSettings} -- Settings for the request.
            logger {Logger} -- A logger to use for logging.

        Yields:
            A stream representing the response(s) from the LLM.
        """
        pass
