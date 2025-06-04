# Copyright (c) Microsoft. All rights reserved.

import copy
from abc import ABC
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

from semantic_kernel.services.ai_service_client_base import AIServiceClientBase

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.contents import StreamingTextContent, TextContent


class TextCompletionClientBase(AIServiceClientBase, ABC):
    """Base class for text completion AI services."""

    # region Internal methods to be implemented by the derived classes

    async def _inner_get_text_contents(
        self,
        prompt: str,
        settings: "PromptExecutionSettings",
    ) -> list["TextContent"]:
        """Send a text completion request to the AI service.

        Args:
            prompt (str): The prompt to send to the LLM.
            settings (PromptExecutionSettings): Settings for the request.

        Returns:
            list[TextContent]: A string or list of strings representing the response(s) from the LLM.
        """
        raise NotImplementedError("The _inner_get_text_contents method is not implemented.")

    async def _inner_get_streaming_text_contents(
        self,
        prompt: str,
        settings: "PromptExecutionSettings",
    ) -> AsyncGenerator[list["StreamingTextContent"], Any]:
        """Send a streaming text request to the AI service.

        Args:
            prompt (str): The prompt to send to the LLM.
            settings (PromptExecutionSettings): Settings for the request.

        Yields:
            list[StreamingTextContent]: A stream representing the response(s) from the LLM.
        """
        # Below is needed for mypy: https://mypy.readthedocs.io/en/stable/more_types.html#asynchronous-iterators
        raise NotImplementedError("The _inner_get_streaming_text_contents method is not implemented.")
        if False:
            yield

    # endregion

    # region Public methods

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
        # Create a copy of the settings to avoid modifying the original settings
        settings = copy.deepcopy(settings)

        return await self._inner_get_text_contents(prompt, settings)

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

    async def get_streaming_text_contents(
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
        # Create a copy of the settings to avoid modifying the original settings
        settings = copy.deepcopy(settings)

        async for contents in self._inner_get_streaming_text_contents(prompt, settings):
            yield contents

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

    # endregion
