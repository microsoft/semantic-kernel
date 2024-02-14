# Copyright (c) Microsoft. All rights reserved.


from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, AsyncIterable, List, Optional

from semantic_kernel.models.ai.chat_completion.chat_history import ChatHistory

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.contents import StreamingTextContent, TextContent


class TextCompletionClientBase(ABC):
    """Base class for text completion AI services."""

    @abstractmethod
    async def complete(
        self,
        chat_history: ChatHistory,
        settings: "PromptExecutionSettings",
        logger: Optional[Any] = None,
    ) -> List["TextContent"]:
        """
        This is the method that is called from the kernel to get a response from a text-optimized LLM.

        Arguments:
            chat_history {ChatHistory} -- The chat history to send to the LLM.
            settings {PromptExecutionSettings} -- Settings for the request.
            logger {Logger} -- A logger to use for logging (deprecated).

            Returns:
                Union[str, List[str]] -- A string or list of strings representing the response(s) from the LLM.
        """

    @abstractmethod
    async def complete_stream(
        self,
        chat_history: ChatHistory,
        settings: "PromptExecutionSettings",
        logger: Optional[Any] = None,
    ) -> AsyncIterable[List["StreamingTextContent"]]:
        """
        This is the method that is called from the kernel to get a stream response from a text-optimized LLM.

        Arguments:
            chat_history {ChatHistory} -- The chat history to send to the LLM.
            settings {PromptExecutionSettings} -- Settings for the request.
            logger {Logger} -- A logger to use for logging (deprecated).

        Yields:
            A stream representing the response(s) from the LLM.
        """
