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
        """This is the method that is called from the kernel to get a response from a text-optimized LLM.

        Args:
            prompt (str): The prompt to send to the LLM.
            settings (PromptExecutionSettings): Settings for the request.

        Returns:
            list[TextContent]: A string or list of strings representing the response(s) from the LLM.
        """

    @abstractmethod
    def get_streaming_text_contents(
        self,
        prompt: str,
        settings: "PromptExecutionSettings",
    ) -> AsyncGenerator[list["StreamingTextContent"], Any]:
        """This is the method that is called from the kernel to get a stream response from a text-optimized LLM.

        Args:
            prompt (str): The prompt to send to the LLM.
            settings (PromptExecutionSettings): Settings for the request.

        Yields:
            list[StreamingTextContent]: A stream representing the response(s) from the LLM.
        """
        ...
