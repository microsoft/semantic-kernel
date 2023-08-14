# Copyright (c) Microsoft. All rights reserved.

# from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, AsyncGenerator

from semantic_kernel.connectors.ai.ai_service_client_base import AIServiceClientBase

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.complete_request_settings import (
        CompleteRequestSettings,
    )
    from semantic_kernel.models.completion_result import CompletionResult


class TextCompletionClientBase(AIServiceClientBase):
    """Base class for all Text Completion Services"""

    async def complete_async(
        self,
        prompt: str,
        settings: "CompleteRequestSettings",
    ) -> "CompletionResult":
        """
        This is the method that is called from the kernel to get a response from a text-optimized LLM.

        Arguments:
            prompt {str} -- The prompt to send to the LLM.
            settings {CompleteRequestSettings} -- Settings for the request.
            logger {Logger} -- A logger to use for logging.

            Returns:
                CompletionResult -- A string or list of strings representing the response(s) from the LLM.
        """
        raise NotImplementedError(
            "complete_async has to be implemented by the used subclass."
        )

    async def complete_stream_async(
        self,
        prompt: str,
        settings: "CompleteRequestSettings",
    ) -> AsyncGenerator["CompletionResult", None]:
        """
        This is the method that is called from the kernel to get a stream response from a text-optimized LLM.

        Arguments:
            prompt {str} -- The prompt to send to the LLM.
            settings {CompleteRequestSettings} -- Settings for the request.
            logger {Logger} -- A logger to use for logging.

        Yields:
            A stream representing the response(s) from the LLM.
        """
        raise NotImplementedError(
            "complete_stream_async has to be implemented by the used subclass."
        )
