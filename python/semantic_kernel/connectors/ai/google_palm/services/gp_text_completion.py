# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import List, Optional, Union

import google.generativeai as palm

from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.complete_request_settings import (
    CompleteRequestSettings,
)
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)


class GooglePalmTextCompletion(TextCompletionClientBase):
    _model_id: str
    _api_key: str

    def __init__(self, model_id: str, api_key: str) -> None:
        """
        Initializes a new instance of the GooglePalmTextCompletion class.

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

    async def complete_async(
        self,
        prompt: str,
        request_settings: CompleteRequestSettings,
        logger: Optional[Logger] = None,
    ) -> Union[str, List[str]]:
        response = await self._send_completion_request(prompt, request_settings)

        if request_settings.number_of_responses > 1:
            return [candidate["output"] for candidate in response.candidates]
        else:
            return response.result

    async def complete_stream_async(
        self,
        prompt: str,
        request_settings: CompleteRequestSettings,
        logger: Optional[Logger] = None,
    ):
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
            palm.configure(api_key=self._api_key)
        except Exception as ex:
            raise PermissionError(
                "Google PaLM service failed to configure. Invalid API key provided.",
                ex,
            )
        try:
            response = palm.generate_text(
                model=self._model_id,
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
