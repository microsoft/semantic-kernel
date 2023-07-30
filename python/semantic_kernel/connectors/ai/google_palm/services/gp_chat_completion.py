# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings
from semantic_kernel.connectors.ai.complete_request_settings import CompleteRequestSettings
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
import asyncio

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
            return [candidate['output'] if candidate['output'] is not None else "I don't know." for candidate in response.candidates]
        else:
            if response.last is None:
                return "I don't know." # PaLM returns None if it doesn't know
            else:
                return response.last

    async def complete_chat_stream_async(
        self, messages: List[Tuple[str, str]], request_settings: ChatRequestSettings,
        delay=0.1, output_words=1, context: Optional[str] = None
    ):
        response = await self._send_chat_request(messages, request_settings, context)

        if request_settings.number_of_responses > 1:
            for choice in response.candidates:
                await asyncio.sleep(delay)
                yield choice['output'] if choice['output'] is not None else "I don't know."
        else:
            if response.last is None:
                response = "I don't know.".split() # PaLM returns None if it doesn't know
            else:
                response = response.last.split()
            for i in range(0, len(response), output_words):
                chunk = response[i:i+output_words]
                chunk = " ".join(chunk)
                await asyncio.sleep(delay)
                yield chunk        

    async def complete_async(
        self, prompt: str, request_settings: CompleteRequestSettings
    ) -> Union[str, List[str]]:
        
        prompt_to_message = [("user", prompt)]
        chat_settings = ChatRequestSettings(
            temperature=request_settings.temperature,
            top_p=request_settings.top_p,
            presence_penalty=request_settings.presence_penalty,
            frequency_penalty=request_settings.frequency_penalty,
            max_tokens=request_settings.max_tokens,
            number_of_responses=request_settings.number_of_responses,
            token_selection_biases=request_settings.token_selection_biases,
        )
        response = await self._send_chat_request(
            prompt_to_message, chat_settings
            )
        
        if chat_settings.number_of_responses > 1:
            return [candidate['output'] if candidate['output'] is not None else "I don't know." for candidate in response.candidates]
        else:
            if response.last is None:
                return "I don't know." # PaLM returns None if it doesn't know
            else:
                return response.last

    async def complete_stream_async(
        self, prompt: str, request_settings: CompleteRequestSettings, delay=0.1,
        output_words=1
    ):
        prompt_to_message = [("user", prompt)]
        chat_settings = ChatRequestSettings(
            temperature=request_settings.temperature,
            top_p=request_settings.top_p,
            presence_penalty=request_settings.presence_penalty,
            frequency_penalty=request_settings.frequency_penalty,
            max_tokens=request_settings.max_tokens,
            number_of_responses=request_settings.number_of_responses,
            token_selection_biases=request_settings.token_selection_biases,
        )
        response = await self._send_chat_request(
            prompt_to_message, chat_settings
            )
        
        if request_settings.number_of_responses > 1:
            for choice in response.candidates:
                await asyncio.sleep(delay)
                yield choice['output'] if choice['output'] is not None else "I don't know."
        else:
            if response.last is None:
                response = "I don't know.".split() # PaLM returns None if it doesn't know
            else:
                response = response.last.split()
            for i in range(0, len(response), output_words):
                chunk = response[i:i+output_words]
                chunk = " ".join(chunk)
                await asyncio.sleep(delay)
                yield chunk

    async def _send_chat_request(
        self,
        messages: List[Tuple[str, str]],
        request_settings: ChatRequestSettings,
        context: Optional[str] = None,
    ):
        """
        Completes the given user message. If chat history is needed to provide 
        context, the chat history in messages is concatenated to a string and 
        sent to the API as the context parameter. If len(messages) > 1, and a 
        conversation has not been initiated yet, all messages preceding the 
        last message will be utilized for context. This enables Google PaLM to 
        utilize memory and skills, which are stored in the messages parameter.

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
        if self._message_history is None and context is None: # If the conversation hasn't started yet and no context is provided
            context = ""
            if len(messages) > 1: # Check if we need context from messages
                for index, (role, message) in enumerate(messages):
                    if index < len(messages) - 1:
                        if role == "system":
                            context += message + "\n"
                        else:
                            context += role + ": " + message + "\n"
        print("context", context)
        try:
            if self._message_history is None: 
                response = palm.chat( # Start a new conversation
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
                response = self._message_history.reply( # Continue the conversation
                    messages[-1][1],
                )
            self._message_history = response # Store response object for future use
        except Exception as ex:
            raise AIException(
                AIException.ErrorCodes.ServiceError,
                "Google PaLM service failed to complete the prompt",
                ex,
            )
        return response