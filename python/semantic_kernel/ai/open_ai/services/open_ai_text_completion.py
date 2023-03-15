# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import Any, Optional

from semantic_kernel.ai.ai_exception import AIException
from semantic_kernel.ai.complete_request_settings import CompleteRequestSettings
from semantic_kernel.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.diagnostics.verify import Verify
from semantic_kernel.utils.null_logger import NullLogger


class OpenAITextCompletion(TextCompletionClientBase):
    _model_id: str
    _api_key: str
    _org_id: Optional[str] = None
    _log: Logger

    def __init__(
        self,
        model_id: str,
        api_key: str,
        org_id: Optional[str] = None,
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
        self._org_id = org_id
        self._log = log if log is not None else NullLogger()

    async def complete_simple_async(
        self, prompt: str, request_settings: CompleteRequestSettings
    ) -> str:
        """
        Completes the given prompt. Returns a single string completion.
        Cannot return multiple completions. Cannot return logprobs.

        Arguments:
            prompt {str} -- The prompt to complete.
            request_settings {CompleteRequestSettings} -- The request settings.

        Returns:
            str -- The completed text.
        """
        import openai

        Verify.not_empty(prompt, "The prompt is empty")
        Verify.not_null(request_settings, "The request settings cannot be empty")

        if request_settings.max_tokens < 1:
            raise AIException(
                AIException.ErrorCodes.InvalidRequest,
                "The max tokens must be greater than 0, "
                f"but was {request_settings.max_tokens}",
            )

        if request_settings.number_of_responses != 1:
            raise AIException(
                AIException.ErrorCodes.InvalidRequest,
                "complete_simple_async only supports a single completion, "
                f"but {request_settings.number_of_responses} were requested",
            )

        if request_settings.logprobs != 0:
            raise AIException(
                AIException.ErrorCodes.InvalidRequest,
                "complete_simple_async does not support logprobs, "
                f"but logprobs={request_settings.logprobs} was requested",
            )

        openai.api_key = self._api_key
        if self._org_id is not None:
            openai.organization = self._org_id

        try:
            response: Any = await openai.Completion.acreate(
                model=self._model_id,
                prompt=prompt,
                temperature=request_settings.temperature,
                top_p=request_settings.top_p,
                presence_penalty=request_settings.presence_penalty,
                frequency_penalty=request_settings.frequency_penalty,
                max_tokens=request_settings.max_tokens,
                stop=(
                    request_settings.stop_sequences
                    if len(request_settings.stop_sequences) > 0
                    else None
                ),
            )
        except Exception as ex:
            raise AIException(
                AIException.ErrorCodes.ServiceError,
                "OpenAI service failed to complete the prompt",
                ex,
            )

        # TODO: tracking on token counts/etc.

        return response.choices[0].text

    # TODO: complete w/ multiple...
