# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Any, List, Optional, Union

import google.generativeai as palm
from pydantic import constr

from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
from semantic_kernel.connectors.ai.ai_service_client_base import AIServiceClientBase
from semantic_kernel.connectors.ai.google_palm.gp_request_settings import (
    GooglePalmTextRequestSettings,
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
            logger.warning("The `log` parameter is deprecated. Please use the `logging` module instead.")

    async def complete_async(
        self,
        prompt: str,
        request_settings: GooglePalmTextRequestSettings,
        logger: Optional[Any] = None,
    ) -> Union[str, List[str]]:
        request_settings.prompt = prompt
        if not request_settings.ai_model_id:
            request_settings.ai_model_id = self.ai_model_id
        try:
            palm.configure(api_key=self.api_key)
        except Exception as ex:
            raise PermissionError(
                "Google PaLM service failed to configure. Invalid API key provided.",
                ex,
            )
        try:
            response = palm.generate_text(**request_settings.prepare_settings_dict())
        except Exception as ex:
            raise AIException(
                AIException.ErrorCodes.ServiceError,
                "Google PaLM service failed to complete the prompt",
                ex,
            )
        if request_settings.candidate_count > 1:
            return [candidate["output"] for candidate in response.candidates]
        return response.result

    async def complete_stream_async(
        self,
        prompt: str,
        request_settings: GooglePalmTextRequestSettings,
        logger: Optional[Any] = None,
    ):
        raise NotImplementedError("Google Palm API does not currently support streaming")

    def get_request_settings_class(self) -> "AIRequestSettings":
        """Create a request settings object."""
        return GooglePalmTextRequestSettings
