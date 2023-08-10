# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from logging import Logger
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings
    from semantic_kernel.semantic_functions.chat_prompt_template import ChatMessage


class ChatCompletionClientBase(ABC):
    _has_function_completion: bool = False

    @abstractmethod
    async def complete_chat_async(
        self,
        messages: List["ChatMessage"],
        settings: "ChatRequestSettings",
        logger: Optional[Logger] = None,
    ) -> Union[str, List[str]]:
        """
        This is the method that is called from the kernel to get a response from a chat-optimized LLM.

        Arguments:
            messages {List[ChatMessage]} -- A list of chat messages, that can be rendered into a set of messages, from system, user, assistant and function.
            settings {ChatRequestSettings} -- Settings for the request.
            logger {Logger} -- A logger to use for logging.

        Returns:
            Union[str, List[str]] -- A string or list of strings representing the response(s) from the LLM.
        """
        pass

    @abstractmethod
    async def complete_chat_stream_async(
        self,
        messages: List["ChatMessage"],
        settings: "ChatRequestSettings",
        logger: Optional[Logger] = None,
    ):
        """
        This is the method that is called from the kernel to get a stream response from a chat-optimized LLM.

        Arguments:
            messages {List[ChatMessage]} -- A list of chat messages, that can be rendered into a set of messages, from system, user, assistant and function.
            settings {ChatRequestSettings} -- Settings for the request.
            logger {Logger} -- A logger to use for logging.

        Yields:
            A stream representing the response(s) from the LLM.
        """
        pass

    async def complete_chat_with_functions_async(
        self,
        messages: List["ChatMessage"],
        functions: List[Dict[str, Any]],
        request_settings: "ChatRequestSettings",
    ) -> Union[
        Tuple[Optional[str], Optional[Dict]], List[Tuple[Optional[str], Optional[Dict]]]
    ]:
        """
        This is the method that is called from the kernel to get a response from a chat-optimized LLM.

        Arguments:
            messages {List[ChatMessage]} -- A list of chat messages, that can be rendered into a set of messages, from system, user, assistant and function.
            functions {List[Dict[str, Any]]} -- A list of function definitions that the endpoint can refer to.
            settings {ChatRequestSettings} -- Settings for the request.
            logger {Logger} -- A logger to use for logging.

        Returns:
            Union[
                Tuple[Optional[str], Optional[Dict]], List[Tuple[Optional[str], Optional[Dict]]]
            ] -- A tuple or list of tuples consisting of the completion message and the function_call result.
        """
        if not self._has_function_completion:
            return await self.complete_chat_async(messages, request_settings)
