# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import (
    AsyncGenerator,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)

from semantic_kernel.connectors.ai import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai.models.chat.function_call import FunctionCall
from semantic_kernel.connectors.ai.open_ai.open_ai_request_settings import (
    OpenAIRequestSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import (
    OpenAIHandler,
)
from semantic_kernel.connectors.ai.open_ai.utils import _parse_choices, _parse_message

logger: logging.Logger = logging.getLogger(__name__)


class OpenAIChatCompletionBase(OpenAIHandler, ChatCompletionClientBase):
    async def complete_chat_async(
        self,
        messages: List[Dict[str, str]],
        settings: OpenAIRequestSettings,
        **kwargs,
    ) -> Union[
        Tuple[Optional[str], Optional[FunctionCall]],
        List[Tuple[Optional[str], Optional[FunctionCall]]],
    ]:
        """Executes a chat completion request and returns the result.

        Arguments:
            messages {List[Tuple[str,str]]} -- The messages to use for the chat completion.
            settings {OpenAIRequestSettings} -- The settings to use for the chat completion request.
            logger {Optional[Logger]} -- The logger instance to use. (Deprecated)

        Returns:
            Union[str, List[str]] -- The completion result(s).
        """
        settings.messages = messages
        settings.stream = False
        if settings.ai_model_id is None:
            settings.ai_model_id = self.ai_model_id
        response = await self._send_request(request_settings=settings)

        if len(response.choices) == 1:
            return _parse_message(response.choices[0].message)
        else:
            return [_parse_message(choice.message) for choice in response.choices]

    async def complete_chat_stream_async(
        self,
        messages: List[Dict[str, str]],
        settings: OpenAIRequestSettings,
        **kwargs,
    ) -> AsyncGenerator[Union[str, List[str]], None]:
        """Executes a chat completion request and returns the result.

        Arguments:
            messages {List[Tuple[str,str]]} -- The messages to use for the chat completion.
            settings {OpenAIRequestSettings} -- The settings to use for the chat completion request.
            logger {Optional[Logger]} -- The logger instance to use. (Deprecated)

        Returns:
            Union[str, List[str]] -- The completion result(s).
        """
        settings.messages = messages
        settings.stream = True
        if settings.ai_model_id is None:
            settings.ai_model_id = self.ai_model_id
        response = await self._send_request(request_settings=settings)

        # parse the completion text(s) and yield them
        async for chunk in response:
            if len(chunk.choices) == 0:
                continue
            # if multiple responses are requested, keep track of them
            if settings.number_of_responses > 1:
                completions = [""] * settings.number_of_responses
                for choice in chunk.choices:
                    text, index = _parse_choices(choice)
                    completions[index] = text
                yield completions
            # if only one response is requested, yield it
            else:
                text, index = _parse_choices(chunk.choices[0])
                yield text
