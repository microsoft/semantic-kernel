# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.ai.complete_request_settings import (
    CompleteRequestSettings,
)
from typing import Union, List
from semantic_kernel.connectors.ai.ai_exception import AIException
import google.generativeai as palm


class GooglePalmTextCompletion():
    _model_id: str
    _api_key: str

    def __init__(
        self,
        model_id: str,
        api_key: str
    ) -> None:
        """
        Initializes a new instance of the GooglePalmTextCompletion class.

        Arguments:
            model_id {str} -- GooglePalm model name, see
            https://developers.generativeai.google/models/language
            api_key {str} -- GooglePalm API key, see
            https://developers.generativeai.google/products/palm
        """
        self._model_id = model_id
        self._api_key = api_key

        try:
            import google.generativeai as palm
        except (ImportError, ModuleNotFoundError):
            raise ImportError(
                "Please ensure that google.generativeai is installed to use GooglePalmTextCompletion"
            )

    async def complete_async(
        self, prompt: str, request_settings: CompleteRequestSettings
    ) -> Union[str, List[str]]:
        
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
        if request_settings.logprobs != 0:
            raise AIException(
                AIException.ErrorCodes.InvalidRequest,
                "complete_async does not support logprobs, "
                f"but logprobs={request_settings.logprobs} was requested",
            )
        try:
            palm.configure(api_key=self._api_key)
        except Exception as ex:
            raise PermissionError (
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
                candidate_count=request_settings.candidate_count, 
                top_p=request_settings.top_p,            
            )
        except Exception as ex:
            raise AIException(
                AIException.ErrorCodes.ServiceError,
                "Google PaLM service failed to complete the prompt",
                ex,
            )
        if request_settings.candidate_count > 1:
            return [candidate['output'] for candidate in response.candidates]
        else:
            return response.result