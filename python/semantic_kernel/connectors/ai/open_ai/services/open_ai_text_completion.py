# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import Any, Optional

import openai

from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.complete_request_settings import (
    CompleteRequestSettings,
)
from semantic_kernel.connectors.ai.open_ai.models.open_ai_completion_result import (
    OpenAICompletionResult,
)
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)


class OpenAITextCompletion(TextCompletionClientBase):
    _model_id: str
    _api_key: str
    _api_type: Optional[str] = None
    _api_version: Optional[str] = None
    _endpoint: Optional[str] = None
    _org_id: Optional[str] = None

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
        super().__init__(log=log)

    async def complete_async(
        self, prompt: str, request_settings: CompleteRequestSettings
    ) -> OpenAICompletionResult:
        return await self._send_completion_request(prompt, request_settings)

    async def complete_stream_async(
        self, prompt: str, request_settings: CompleteRequestSettings
    ):
        async for response in self._send_completion_stream_request(
            prompt, request_settings
        ):
            yield response

    async def _send_completion_request(
        self, prompt: str, request_settings: CompleteRequestSettings
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
        self._check_prompt_and_settings(prompt, request_settings)

        try:
            response: Any = await openai.Completion.acreate(
                **self._get_model_args(),
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
                stream=False,
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
        try:
            completion_result = OpenAICompletionResult.from_openai_object(response)
            self._log.debug(completion_result)
            if completion_result.usage:
                self.add_usage(completion_result.usage)
            return completion_result
        except Exception as ex:
            raise AIException(
                AIException.ErrorCodes.ServiceError,
                "Failed to parse the completion response",
                ex,
            ) from ex

    async def _send_completion_stream_request(
        self, prompt: str, request_settings: CompleteRequestSettings
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
        self._check_prompt_and_settings(prompt, request_settings)

        try:
            response: Any = await openai.Completion.acreate(
                **self._get_model_args(),
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
                stream=True,
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
        result_chunks = []
        async for chunk in response:
            if chunk.id:
                try:
                    result_chunk = OpenAICompletionResult.from_openai_object(
                        chunk, True
                    )
                    yield result_chunk
                    result_chunks.append(result_chunk)
                    self._log.debug(result_chunk)
                except Exception as exc:
                    self._log.warning(exc)

        final_result = OpenAICompletionResult.from_chunk_list(result_chunks)
        if final_result.usage:
            self.add_usage(final_result.usage)
        yield final_result

    def _get_model_args(self):
        model_args = {}
        if self._api_type in ["azure", "azure_ad"]:
            model_args["engine"] = self._model_id
        else:
            model_args["model"] = self._model_id
        return model_args

    def _check_prompt_and_settings(self, prompt, request_settings):
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
