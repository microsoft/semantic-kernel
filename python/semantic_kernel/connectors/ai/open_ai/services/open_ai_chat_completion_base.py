# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import TYPE_CHECKING, AsyncGenerator, List, Optional, Tuple, Union

from semantic_kernel.connectors.ai import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import (
    OpenAIHandler,
)

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings


class OpenAIChatCompletionBase(OpenAIHandler, ChatCompletionClientBase):
    async def complete_chat_async(
        self,
        messages: List[Tuple[str, str]],
        settings: "ChatRequestSettings",
        logger: Optional[Logger] = None,
    ) -> Union[str, List[str]]:
        """Executes a chat completion request and returns the result.

        Arguments:
            messages {List[Tuple[str,str]]} -- The messages to use for the chat completion.
            settings {ChatRequestSettings} -- The settings to use for the chat completion request.
            logger {Optional[Logger]} -- The logger instance to use. (Optional)

        Returns:
            Union[str, List[str]] -- The completion result(s).
        """
        response = await self._send_request(
            messages=messages, request_settings=settings, stream=False
        )

        if len(response.choices) == 1:
            return response.choices[0].message.content
        else:
            return [choice.message.content for choice in response.choices]

    async def complete_chat_stream_async(
        self,
        messages: List[Tuple[str, str]],
        settings: "ChatRequestSettings",
        logger: Optional[Logger] = None,
    ) -> AsyncGenerator[Union[str, List[str]], None]:
        """Executes a chat completion request and returns the result.

        Arguments:
            messages {List[Tuple[str,str]]} -- The messages to use for the chat completion.
            settings {ChatRequestSettings} -- The settings to use for the chat completion request.
            logger {Optional[Logger]} -- The logger instance to use. (Optional)

        Returns:
            Union[str, List[str]] -- The completion result(s).
        """
        response = await self._send_request(
            messages=messages, request_settings=settings, stream=True
        )

        # parse the completion text(s) and yield them
        async for chunk in response:
            text, index = self._parse_choices(chunk)
            # if multiple responses are requested, keep track of them
            if settings.number_of_responses > 1:
                completions = [""] * settings.number_of_responses
                completions[index] = text
                yield completions
            # if only one response is requested, yield it
            else:
                yield text

    @staticmethod
    def _parse_choices(chunk):
        message = ""
        if "role" in chunk.choices[0].delta:
            message += chunk.choices[0].delta.role + ": "
        if "content" in chunk.choices[0].delta:
            message += chunk.choices[0].delta.content

        index = chunk.choices[0].index
        return message, index
