# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import TYPE_CHECKING, AsyncGenerator, List, Optional, Union

from openai.types.completion import Completion

from semantic_kernel.connectors.ai import TextCompletionClientBase
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import (
    OpenAIHandler,
)

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.complete_request_settings import (
        CompleteRequestSettings,
    )


class OpenAITextCompletionBase(TextCompletionClientBase, OpenAIHandler):
    async def complete_async(
        self,
        prompt: str,
        settings: "CompleteRequestSettings",
        logger: Optional[Logger] = None,
    ) -> Union[str, List[str]]:
        """Executes a completion request and returns the result.

        Arguments:
            prompt {str} -- The prompt to use for the completion request.
            settings {CompleteRequestSettings} -- The settings to use for the completion request.
            logger {Optional[Logger]} -- The logger instance to use. (Optional)

        Returns:
            Union[str, List[str]] -- The completion result(s).
        """
        response = await self._send_request(
            prompt=prompt, request_settings=settings, stream=False
        )

        if isinstance(response, Completion):
            if len(response.choices) == 1:
                return response.choices[0].text
            return [choice.text for choice in response.choices]
        if len(response.choices) == 1:
            return response.choices[0].message.content
        return [choice.message.content for choice in response.choices]

    async def complete_stream_async(
        self,
        prompt: str,
        settings: "CompleteRequestSettings",
        logger: Optional[Logger] = None,
    ) -> AsyncGenerator[Union[str, List[str]], None]:
        """
        Executes a completion request and streams the result.
        Supports both chat completion and text completion.

        Arguments:
            prompt {str} -- The prompt to use for the completion request.
            settings {CompleteRequestSettings} -- The settings to use for the completion request.
            logger {Optional[Logger]} -- The logger instance to use. (Optional)

        Returns:
            Union[str, List[str]] -- The completion result(s).
        """
        response = await self._send_request(
            prompt=prompt, request_settings=settings, stream=True
        )

        async for partial in response:
            if len(partial.choices) == 0:
                continue

            if settings.number_of_responses > 1:
                completions = [""] * settings.number_of_responses
                for choice in partial.choices:
                    if hasattr(choice, "delta") and hasattr(
                        choice.delta, "content"
                    ):  # Chat completion
                        completions[choice.index] = choice.delta.content
                    elif hasattr(choice, "text"):  # Text completion
                        completions[choice.index] = choice.text
                if any(completions):
                    yield completions
            else:
                if hasattr(partial.choices[0], "delta") and hasattr(
                    partial.choices[0].delta, "content"
                ):  # Chat completion
                    content = partial.choices[0].delta.content
                    if content:
                        yield content
                elif hasattr(partial.choices[0], "text"):  # Text completion
                    text = partial.choices[0].text
                    if text.strip():  # Exclude empty or whitespace-only text
                        yield text
