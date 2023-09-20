# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import TYPE_CHECKING, List, Optional, Union

from semantic_kernel.connectors.ai import TextCompletionClientBase
from semantic_kernel.connectors.ai.open_ai.services.base_open_ai_functions import (
    OpenAIServiceCalls,
)

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.complete_request_settings import (
        CompleteRequestSettings,
    )


class BaseTextCompletion(TextCompletionClientBase, OpenAIServiceCalls):
    async def complete_async(
        self,
        prompt: str,
        settings: "CompleteRequestSettings",
        logger: Optional[Logger] = None,
    ) -> Union[str, List[str]]:
        response = await self._send_request(
            prompt=prompt, request_settings=settings, stream=False
        )

        if len(response.choices) == 1:
            return response.choices[0].text
        else:
            return [choice.text for choice in response.choices]

    async def complete_stream_async(
        self,
        prompt: str,
        settings: "CompleteRequestSettings",
        logger: Optional[Logger] = None,
    ):
        response = await self._send_request(
            prompt=prompt, request_settings=settings, stream=True
        )

        async for chunk in response:
            if settings.number_of_responses > 1:
                for choice in chunk.choices:
                    completions = [""] * settings.number_of_responses
                    completions[choice.index] = choice.text
                    yield completions
            else:
                yield chunk.choices[0].text
