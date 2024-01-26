# Copyright (c) Microsoft. All rights reserved.


from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, AsyncIterable, List, Optional

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
    from semantic_kernel.models.contents import StreamingTextContent, TextContent


class TextCompletionClientBase(ABC):
    """Base class for text completion AI services."""

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        settings: "AIRequestSettings",
        logger: Optional[Any] = None,
    ) -> List["TextContent"]:
        """
        This is the method that is called from the kernel to get a response from a text-optimized LLM.

        Arguments:
            prompt {str} -- The prompt to send to the LLM.
            settings {AIRequestSettings} -- Settings for the request.
            logger {Logger} -- A logger to use for logging (deprecated).

            Returns:
                Union[str, List[str]] -- A string or list of strings representing the response(s) from the LLM.
        """

    @abstractmethod
    async def complete_stream(
        self,
        prompt: str,
        settings: "AIRequestSettings",
        logger: Optional[Any] = None,
    ) -> AsyncIterable[List["StreamingTextContent"]]:
        """
        This is the method that is called from the kernel to get a stream response from a text-optimized LLM.

        Arguments:
            prompt {str} -- The prompt to send to the LLM.
            settings {AIRequestSettings} -- Settings for the request.
            logger {Logger} -- A logger to use for logging (deprecated).

        Yields:
            A stream representing the response(s) from the LLM.
        """
