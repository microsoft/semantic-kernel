# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncGenerator,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)

from semantic_kernel.connectors.ai import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai.models.chat.function_call import FunctionCall
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import (
    OpenAIHandler,
)
from semantic_kernel.connectors.ai.open_ai.utils import _parse_message

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings


class OpenAIChatCompletionBase(OpenAIHandler, ChatCompletionClientBase):
    async def complete_chat_async(
        self,
        messages: List[Dict[str, str]],
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

    async def complete_chat_with_functions_async(
        self,
        messages: List[Dict[str, str]],
        functions: List[Dict[str, Any]],
        request_settings: "ChatRequestSettings",
        logger: Optional[Logger] = None,
    ) -> Union[
        Tuple[Optional[str], Optional[FunctionCall]],
        List[Tuple[Optional[str], Optional[FunctionCall]]],
    ]:
        """Executes a chat completion request and returns the result.

        Arguments:
            messages {List[Tuple[str,str]]} -- The messages to use for the chat completion.
            functions {List[Dict[str, Any]]} -- The functions to use for the chat completion.
            settings {ChatRequestSettings} -- The settings to use for the chat completion request.
            logger {Optional[Logger]} -- The logger instance to use. (Optional)

        Returns:
            Union[str, List[str]] -- The completion result(s).
        """

        response = await self._send_request(
            messages=messages,
            request_settings=request_settings,
            stream=False,
            functions=functions,
        )

        if len(response.choices) == 1:
            return _parse_message(response.choices[0].message, self.log)
        else:
            return [
                _parse_message(choice.message, self.log) for choice in response.choices
            ]

    async def complete_chat_stream_async(
        self,
        messages: List[Dict[str, str]],
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
            if len(chunk.choices) == 0:
                continue
            # if multiple responses are requested, keep track of them
            if settings.number_of_responses > 1:
                completions = [""] * settings.number_of_responses
                for choice in chunk.choices:
                    text, index = self._parse_choices(choice)
                    completions[index] = text
                yield completions
            # if only one response is requested, yield it
            else:
                text, index = self._parse_choices(chunk.choices[0])
                yield text

    @staticmethod
    def _parse_choices(choice) -> Tuple[str, int]:
        message = ""
        if choice.delta.content:
            message += choice.delta.content

        return message, choice.index
