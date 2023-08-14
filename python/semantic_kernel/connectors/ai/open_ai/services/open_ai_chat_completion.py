# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import Any, AsyncGenerator, Dict, List, Optional

import openai

from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings
from semantic_kernel.connectors.ai.complete_request_settings import (
    CompleteRequestSettings,
)
from semantic_kernel.connectors.ai.open_ai.models.open_ai_chat_completion_result import (
    OpenAIChatCompletionResult,
)
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)
from semantic_kernel.models.chat.chat_message import ChatMessage


class OpenAIChatCompletion(ChatCompletionClientBase, TextCompletionClientBase):
    _model_id: str
    _api_key: str
    _org_id: Optional[str] = None
    _api_type: Optional[str] = None
    _api_version: Optional[str] = None
    _endpoint: Optional[str] = None

    def __init__(
        self,
        model_id: str,
        api_key: str,
        org_id: Optional[str] = None,
        api_type: Optional[str] = None,
        api_version: Optional[str] = None,
        endpoint: Optional[str] = None,
        log: Optional[Logger] = None,
    ) -> None:
        """
        Initializes a new instance of the OpenAIChatCompletion class.

        Arguments:
            model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            api_key {str} -- OpenAI API key, see
                https://platform.openai.com/account/api-keys
            org_id {Optional[str]} -- OpenAI organization ID.
                This is usually optional unless your
                account belongs to multiple organizations.
        """
        self._model_id = model_id
        self._api_key = api_key
        self._org_id = org_id
        self._api_type = api_type
        self._api_version = api_version
        self._endpoint = endpoint
        self._messages = []
        super().__init__(log=log)

    async def complete_chat_async(
        self,
        messages: List[Dict[str, str]],
        request_settings: ChatRequestSettings,
    ) -> OpenAIChatCompletionResult:
        return await self._send_chat_request(messages, request_settings)

    async def complete_chat_stream_async(
        self,
        messages: List[Dict[str, str]],
        request_settings: ChatRequestSettings,
    ) -> AsyncGenerator[OpenAIChatCompletionResult, None]:
        async for response in self._send_chat_stream_request(
            messages, request_settings
        ):
            yield response

    async def _send_chat_request(
        self,
        messages: List[Dict[str, str]],
        request_settings: ChatRequestSettings,
    ) -> OpenAIChatCompletionResult:
        """
        Completes the given user message with an asynchronous stream.

        Arguments:
            messages {List[Dict[str,str]]} -- The chat history of messages to complete.
            request_settings {ChatRequestSettings} -- The request settings.

        Returns:
            OpenAIChatCompletionResult -- The completion result.
        """
        self._check_messages_and_settings(messages, request_settings)
        try:
            response: Any = await openai.ChatCompletion.acreate(
                **self._get_model_args(),
                api_key=self._api_key,
                api_type=self._api_type,
                api_base=self._endpoint,
                api_version=self._api_version,
                organization=self._org_id,
                messages=messages,
                temperature=request_settings.temperature,
                top_p=request_settings.top_p,
                presence_penalty=request_settings.presence_penalty,
                frequency_penalty=request_settings.frequency_penalty,
                max_tokens=request_settings.max_tokens,
                n=request_settings.number_of_responses,
                stream=False,
                logit_bias=(
                    request_settings.token_selection_biases
                    if request_settings.token_selection_biases is not None
                    and len(request_settings.token_selection_biases) > 0
                    else {}
                ),
            )
        except Exception as ex:
            raise AIException(
                AIException.ErrorCodes.ServiceError,
                "OpenAI service failed to complete the chat",
                ex,
            ) from ex
        try:
            chat_result = OpenAIChatCompletionResult.from_openai_object(response)
            self._log.debug(chat_result)
            if chat_result.usage:
                self.add_usage(chat_result.usage)
            return chat_result
        except Exception as ex:
            raise AIException(
                AIException.ErrorCodes.ServiceError,
                "Failed to parse the completion response",
                ex,
            ) from ex

    async def _send_chat_stream_request(
        self,
        messages: List[Dict[str, str]],
        request_settings: ChatRequestSettings,
    ) -> AsyncGenerator[OpenAIChatCompletionResult, None]:
        """
        Completes the given user message with an asynchronous stream.

        Arguments:
            messages {List[Dict[str,str]]} -- The chat history of messages to complete.
            request_settings {ChatRequestSettings} -- The request settings.

        Returns:
            AsyncGenerator[OpenAIChatCompletionResult, None] --
                A generator for the completion delta results and finally the full list of results.
        """
        self._check_messages_and_settings(messages, request_settings)

        try:
            response: Any = await openai.ChatCompletion.acreate(
                **self._get_model_args(),
                api_key=self._api_key,
                api_type=self._api_type,
                api_base=self._endpoint,
                api_version=self._api_version,
                organization=self._org_id,
                messages=messages,
                temperature=request_settings.temperature,
                top_p=request_settings.top_p,
                presence_penalty=request_settings.presence_penalty,
                frequency_penalty=request_settings.frequency_penalty,
                max_tokens=request_settings.max_tokens,
                n=request_settings.number_of_responses,
                stream=True,
                logit_bias=(
                    request_settings.token_selection_biases
                    if request_settings.token_selection_biases is not None
                    and len(request_settings.token_selection_biases) > 0
                    else {}
                ),
            )
        except Exception as ex:
            raise AIException(
                AIException.ErrorCodes.ServiceError,
                "OpenAI service failed to complete the chat",
                ex,
            ) from ex

        chat_result_chunks = []
        async for chunk in response:
            if "id" in chunk and chunk.id:
                try:
                    chat_result_chunk = OpenAIChatCompletionResult.from_openai_object(
                        chunk, True
                    )
                    yield chat_result_chunk
                    chat_result_chunks.append(chat_result_chunk)
                    self._log.debug(chat_result_chunk)
                except Exception as exc:
                    self._log.warning(exc)
                    continue
        final_result = OpenAIChatCompletionResult.from_chunk_list(chat_result_chunks)
        if final_result.usage:
            self.add_usage(final_result.usage)
        yield final_result

    def _check_messages_and_settings(self, messages, request_settings):
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

        if messages[-1]["role"] != "user":
            raise AIException(
                AIException.ErrorCodes.InvalidRequest,
                "The last message must be from the user",
            )

    def _get_model_args(self) -> Dict[str, str]:
        if self._api_type in ["azure", "azure_ad"]:
            return {"engine": self._model_id}

        return {"model": self._model_id}

    async def complete_async(
        self,
        prompt: str,
        settings: "CompleteRequestSettings",
    ) -> OpenAIChatCompletionResult:
        """
        This is the method that is called from the kernel to get a response from a text-optimized LLM.

        Arguments:
            prompt {str} -- The prompt to send to the LLM.
            settings {CompleteRequestSettings} -- Settings for the request.
            logger {Logger} -- A logger to use for logging.

        Returns:
            ChatCompletionResult -- A object with all the results from the LLM.
        """
        message = ChatMessage(role="user", fixed_content=prompt)
        return await self.complete_chat_async(
            [message.as_dict()],
            ChatRequestSettings(
                temperature=settings.temperature,
                top_p=settings.top_p,
                presence_penalty=settings.presence_penalty,
                frequency_penalty=settings.frequency_penalty,
                max_tokens=settings.max_tokens,
                number_of_responses=settings.number_of_responses,
                token_selection_biases=settings.token_selection_biases,
            ),
        )

    async def complete_stream_async(
        self,
        prompt: str,
        settings: "CompleteRequestSettings",
    ) -> AsyncGenerator[OpenAIChatCompletionResult, None]:
        """
        This is the method that is called from the kernel to get a stream response from a text-optimized LLM.

        Arguments:
            prompt {str} -- The prompt to send to the LLM.
            settings {CompleteRequestSettings} -- Settings for the request.
            logger {Logger} -- A logger to use for logging.

        Yields:
            A stream representing LLM completion results.
        """
        message = ChatMessage(role="user", fixed_content=prompt)
        async for response in self.complete_chat_stream_async(
            [message.as_dict()],
            ChatRequestSettings(
                temperature=settings.temperature,
                top_p=settings.top_p,
                presence_penalty=settings.presence_penalty,
                frequency_penalty=settings.frequency_penalty,
                max_tokens=settings.max_tokens,
                number_of_responses=settings.number_of_responses,
                token_selection_biases=settings.token_selection_biases,
            ),
        ):
            yield response
