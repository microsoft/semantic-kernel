# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from typing import Union, List, Tuple
from semantic_kernel.connectors.ai.ai_exception import AIException
import google.generativeai as palm
import asyncio

class GooglePalmChatCompletion(ChatCompletionClientBase):
    _model_id: str
    _api_key: str

    def __init__(
        self,
        model_id: str,
        api_key: str
    ) -> None:
        """
        Initializes a new instance of the GooglePalmChatCompletion class.

        Arguments:
            model_id {str} -- GooglePalm model name, see
            https://developers.generativeai.google/models/language
            api_key {str} -- GooglePalm API key, see
            https://developers.generativeai.google/products/palm
        """
        if not api_key:
            raise ValueError("The Google PaLM API key cannot be `None` or empty`")
        
        self._model_id = model_id
        self._api_key = api_key

    async def complete_chat_async(
        self, messages: List[Tuple[str, str]], request_settings: ChatRequestSettings
    ) -> Union[str, List[str]]:
        response = await self._send_chat_request(messages, request_settings)

        if len(request_settings.number_of_responses) > 1:
            return [candidate['output'] for candidate in response.candidates]
        else:
            return response.last

    async def complete_chat_stream_async(
        self, messages: List[Tuple[str, str]], request_settings: ChatRequestSettings
    ):
        pass

    async def _send_chat_request(
        self,
        messages: List[Tuple[str, str]],
        request_settings: ChatRequestSettings
    ):
        pass