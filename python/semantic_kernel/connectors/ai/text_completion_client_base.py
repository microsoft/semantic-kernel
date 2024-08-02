# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

from semantic_kernel.services.ai_service_client_base import AIServiceClientBase

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.contents import StreamingTextContent, TextContent


class TextCompletionClientBase(AIServiceClientBase, ABC):
    """Base class for text completion AI services."""

    @abstractmethod
    async def get_text_contents(
        self,
        prompt: str,
        settings: "PromptExecutionSettings",
    ) -> list["TextContent"]:
        """Create text contents, in the number specified by the settings.

        Args:
            prompt (str): The prompt to send to the LLM.
            settings (PromptExecutionSettings): Settings for the request.

        Returns:
            list[TextContent]: A string or list of strings representing the response(s) from the LLM.
        """

    async def get_text_content(self, prompt: str, settings: "PromptExecutionSettings") -> "TextContent | None":
        """This is the method that is called from the kernel to get a response from a text-optimized LLM.

        Args:
            prompt (str): The prompt to send to the LLM.
            settings (PromptExecutionSettings): Settings for the request.

        Returns:
            TextContent: A string or list of strings representing the response(s) from the LLM.
        """
        result = await self.get_text_contents(prompt=prompt, settings=settings)
        if result:
            return result[0]
        # this should not happen, should error out before returning an empty list
        return None  # pragma: no cover

    @abstractmethod
    def get_streaming_text_contents(
        self,
        prompt: str,
        settings: "PromptExecutionSettings",
    ) -> AsyncGenerator[list["StreamingTextContent"], Any]:
        """Create streaming text contents, in the number specified by the settings.

        Args:
            prompt (str): The prompt to send to the LLM.
            settings (PromptExecutionSettings): Settings for the request.

        Yields:
            list[StreamingTextContent]: A stream representing the response(s) from the LLM.
        """
        ...

    async def get_streaming_text_content(
        self, prompt: str, settings: "PromptExecutionSettings"
    ) -> AsyncGenerator["StreamingTextContent | None", Any]:
        """This is the method that is called from the kernel to get a stream response from a text-optimized LLM.

        Args:
            prompt (str): The prompt to send to the LLM.
            settings (PromptExecutionSettings): Settings for the request.

        Returns:
            StreamingTextContent: A stream representing the response(s) from the LLM.
        """
        async for contents in self.get_streaming_text_contents(prompt, settings):
            if contents:
                yield contents[0]
            else:
                # this should not happen, should error out before returning an empty list
                yield None  # pragma: no cover
