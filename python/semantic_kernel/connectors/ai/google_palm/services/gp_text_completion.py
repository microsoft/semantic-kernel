# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Any, List, Optional, Union

import google.generativeai as palm
from pydantic import constr

from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.ai_service_client_base import AIServiceClientBase
from semantic_kernel.connectors.ai.complete_request_settings import (
    CompleteRequestSettings,
)
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)

logger: logging.Logger = logging.getLogger(__name__)


class GooglePalmTextCompletion(TextCompletionClientBase, AIServiceClientBase):
    api_key: constr(strip_whitespace=True, min_length=1)

    def __init__(self, ai_model_id: str, api_key: str, log: Optional[Any] = None):
        """
        Initializes a new instance of the GooglePalmTextCompletion class.

        Arguments:
            ai_model_id {str} -- GooglePalm model name, see
                https://developers.generativeai.google/models/language
            api_key {str} -- GooglePalm API key, see
                https://developers.generativeai.google/products/palm
            log {Optional[Any]} -- The logger instance to use. (Optional) (Deprecated)
        """
        super().__init__(ai_model_id=ai_model_id, api_key=api_key)
        if log:
            logger.warning(
                "The `log` parameter is deprecated. Please use the `logging` module instead."
            )

    async def complete_async(
        self,
        prompt: str,
        request_settings: CompleteRequestSettings,
        **kwargs,
    ) -> Union[str, List[str]]:
        if kwargs.get("logger"):
            logger.warning(
                "The `logger` parameter is deprecated. Please use the `logging` module instead."
            )
        response = await self._send_completion_request(prompt, request_settings)

        if request_settings.number_of_responses > 1:
            return [candidate["output"] for candidate in response.candidates]
        return response.result

    async def complete_stream_async(
        self,
        prompt: str,
        request_settings: CompleteRequestSettings,
        **kwargs,
    ):
        if kwargs.get("logger"):
            logger.warning(
                "The `logger` parameter is deprecated. Please use the `logging` module instead."
            )
        raise NotImplementedError(
            "Google Palm API does not currently support streaming"
        )

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
        if not prompt:
            raise ValueError("Prompt cannot be `None` or empty")
        if request_settings is None:
            raise ValueError("Request settings cannot be `None`")
        if request_settings.max_tokens < 1:
            raise AIException(
                AIException.ErrorCodes.InvalidRequest,
                "The max tokens must be greater than 0, "
                f"but was {request_settings.max_tokens}",
            )
        try:
            palm.configure(api_key=self.api_key)
        except Exception as ex:
            raise PermissionError(
                "Google PaLM service failed to configure. Invalid API key provided.",
                ex,
            )
        try:
            response = palm.generate_text(
                model=self.ai_model_id,
                prompt=prompt,
                temperature=request_settings.temperature,
                max_output_tokens=request_settings.max_tokens,
                stop_sequences=(
                    request_settings.stop_sequences
                    if request_settings.stop_sequences is not None
                    and len(request_settings.stop_sequences) > 0
                    else None
                ),
                candidate_count=request_settings.number_of_responses,
                top_p=request_settings.top_p,
            )
        except Exception as ex:
            raise AIException(
                AIException.ErrorCodes.ServiceError,
                "Google PaLM service failed to complete the prompt",
                ex,
            )
        return response
