# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import Any, List, Optional, Union

import openai

from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.complete_request_settings import (
    CompleteRequestSettings,
)
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)
from semantic_kernel.utils.null_logger import NullLogger


class OpenAITextCompletion(TextCompletionClientBase):
    _model_id: str
    _api_key: str
    _api_type: Optional[str] = None
    _api_version: Optional[str] = None
    _endpoint: Optional[str] = None
    _org_id: Optional[str] = None
    _log: Logger

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
        Initializes a new instance of the OpenAITextCompletion class.

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
        self._api_type = api_type
        self._api_version = api_version
        self._endpoint = endpoint
        self._org_id = org_id
        self._log = log if log is not None else NullLogger()

    async def complete_async(
        self,
        prompt: str,
        request_settings: CompleteRequestSettings,
        logger: Optional[Logger] = None,
    ) -> Union[str, List[str]]:
        # TODO: tracking on token counts/etc.
        response = await self._send_completion_request(prompt, request_settings, False)

        if len(response.choices) == 1:
            return response.choices[0].text
        else:
            return [choice.text for choice in response.choices]

    # TODO: complete w/ multiple...

    async def complete_stream_async(
        self,
        prompt: str,
        request_settings: CompleteRequestSettings,
        logger: Optional[Logger] = None,
    ):
        response = await self._send_completion_request(prompt, request_settings, True)

        async for chunk in response:
            if request_settings.number_of_responses > 1:
                for choice in chunk.choices:
                    completions = [""] * request_settings.number_of_responses
                    completions[choice.index] = choice.text
                    yield completions
            else:
                yield chunk.choices[0].text

    async def _send_completion_request(
        self, prompt: str, request_settings: CompleteRequestSettings, stream: bool
    ):
        """
        Completes the given prompt. Returns a single string completion.
        Cannot return multiple completions. Cannot return logprobs.

        Arguments:
            prompt {str} -- The prompt to complete.
            request_settings {CompleteRequestSettings} -- The request settings.

        Returns:
            str -- The completed text.
        """
        if not prompt:
            raise ValueError("The prompt cannot be `None` or empty")
        if request_settings is None:
            raise ValueError("The request settings cannot be `None`")

        if request_settings.max_tokens < 1:
            raise AIException(
                AIException.ErrorCodes.InvalidRequest,
                "The max tokens must be greater than 0, "
                f"but was {request_settings.max_tokens}",
            )

        if request_settings.logprobs != 0:
            raise AIException(
                AIException.ErrorCodes.InvalidRequest,
                "complete_async does not support logprobs, "
                f"but logprobs={request_settings.logprobs} was requested",
            )

        model_args = {}
        if self._api_type in ["azure", "azure_ad"]:
            model_args["engine"] = self._model_id
        else:
            model_args["model"] = self._model_id

        try:
            response: Any = await openai.Completion.acreate(
                **model_args,
                api_key=self._api_key,
                api_type=self._api_type,
                api_base=self._endpoint,
                api_version=self._api_version,
                organization=self._org_id,
                prompt=prompt,
                temperature=request_settings.temperature,
                top_p=request_settings.top_p,
                presence_penalty=request_settings.presence_penalty,
                frequency_penalty=request_settings.frequency_penalty,
                max_tokens=request_settings.max_tokens,
                stream=stream,
                n=request_settings.number_of_responses,
                stop=(
                    request_settings.stop_sequences
                    if request_settings.stop_sequences is not None
                    and len(request_settings.stop_sequences) > 0
                    else None
                ),
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
                "OpenAI service failed to complete the prompt",
                ex,
            )
        return response
