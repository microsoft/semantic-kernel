# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import TYPE_CHECKING, List, Optional, Tuple, Union

from semantic_kernel.connectors.ai import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai.services.base_open_ai_functions import (
    OpenAIServiceCalls,
    _parse_choices,
)

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings


class BaseChatCompletion(OpenAIServiceCalls, ChatCompletionClientBase):
    async def complete_chat_async(
        self,
        messages: List[Tuple[str, str]],
        settings: "ChatRequestSettings",
        logger: Optional[Logger] = None,
    ) -> Union[str, List[str]]:
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
    ):
        response = await self._send_request(
            messages=messages, request_settings=settings, stream=True
        )

        # parse the completion text(s) and yield them
        async for chunk in response:
            text, index = _parse_choices(chunk)
            # if multiple responses are requested, keep track of them
            if settings.number_of_responses > 1:
                completions = [""] * settings.number_of_responses
                completions[index] = text
                yield completions
            # if only one response is requested, yield it
            else:
                yield text
