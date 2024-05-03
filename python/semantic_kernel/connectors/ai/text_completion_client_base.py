# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, AsyncGenerator

from semantic_kernel.services.ai_service_client_base import AIServiceClientBase

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.contents import StreamingTextContent, TextContent


class TextCompletionClientBase(AIServiceClientBase, ABC):
    """Base class for text completion AI services."""

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        settings: "PromptExecutionSettings",
    ) -> list["TextContent"]:
        """
        This is the method that is called from the kernel to get a response from a text-optimized LLM.

        Arguments:
            prompt {str} -- The prompt to send to the LLM.
            settings {PromptExecutionSettings} -- Settings for the request.

            Returns:
            list[TextContent] -- A string or list of strings representing the response(s) from the LLM.
        """

    @abstractmethod
    def complete_stream(
        self,
        prompt: str,
        settings: "PromptExecutionSettings",
    ) -> AsyncGenerator[list["StreamingTextContent"], Any]:
        """
        This is the method that is called from the kernel to get a stream response from a text-optimized LLM.

        Arguments:
            prompt {str} -- The prompt to send to the LLM.
            settings {PromptExecutionSettings} -- Settings for the request.

        Yields:
            list[StreamingTextContent] -- A stream representing the response(s) from the LLM.
        """
        ...
