# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from typing import Union, List, Tuple, Optional
from semantic_kernel.connectors.ai.ai_exception import AIException
import google.generativeai as palm
from google.generativeai.types import ChatResponse
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)

class GooglePalmChatCompletion(ChatCompletionClientBase, TextCompletionClientBase):
    _model_id: str
    _api_key: str
    _message_history: ChatResponse

    def __init__(
        self,
        model_id: str,
        api_key: str,
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
        self._message_history = None

    async def complete_chat_async(
        self, messages: List[Tuple[str, str]], request_settings: ChatRequestSettings,
        context: Optional[str] = None
    ) -> Union[str, List[str]]:
        response = await self._send_chat_request(messages, request_settings, context)

        if request_settings.number_of_responses > 1:
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
        request_settings: ChatRequestSettings,
        context: Optional[str] = None,
    ):
        """
        Completes the given user message. If there is a system role in messages,
        it will be used as context. System needs to be the first message in
        messages, otherwise it will not be used. Context can also be provided
        as a separate parameter.

        Arguments:
            user_message {str} -- The message (from a user) to respond to.
            request_settings {ChatRequestSettings} -- The request settings.
            context {str} -- Text that should be provided to the model first, 
            to ground the response. If a system message is provided, it will be
            used as context.

        Returns:
            str -- The completed text.
        """
        if request_settings is None:
            raise ValueError("The request settings cannot be `None`")

        if request_settings.max_tokens < 1:
            raise AIException(
                AIException.ErrorCodes.InvalidRequest,
                "The max tokens must be greater than 0, "
                f"but was {request_settings.max_tokens}",
            )

        if len(messages) <= 0:
            raise AIException(
                AIException.ErrorCodes.InvalidRequest,
                "To complete a chat you need at least one message",
            )

        if messages[-1][0] != "user":
            raise AIException(
                AIException.ErrorCodes.InvalidRequest,
                "The last message must be from the user",
            )
        try:
            palm.configure(api_key=self._api_key)
        except Exception as ex:
            raise PermissionError (
                "Google PaLM service failed to configure. Invalid API key provided.",
                ex,
            )
        if messages[0][0] == "system":
            context = messages[0][1]            
        try:
            if self._message_history is None:
                response = palm.chat(
                    model=self._model_id,
                    context=context,
                    examples=None,
                    temperature=request_settings.temperature,
                    candidate_count=request_settings.number_of_responses,
                    top_p=request_settings.top_p,
                    prompt=None,
                    messages=messages[-1][1],
                )
            else: 
                response = self._message_history.reply(
                    messages[-1][1],
                )
            print("check", response.messages)
            self._message_history = response
        except Exception as ex:
            raise AIException(
                AIException.ErrorCodes.ServiceError,
                "Google PaLM service failed to complete the prompt",
                ex,
            )
        return response