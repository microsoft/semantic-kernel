# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import Any, Dict, Optional

from semantic_kernel.connectors.ai.open_ai.services.base_model_types import (
    OpenAIModelTypes,
)
from semantic_kernel.connectors.ai.open_ai.services.base_open_ai_functions import (
    OpenAIServiceCalls,
)


class BaseOpenAIConfig(OpenAIServiceCalls):
    api_type: str
    org_id: Optional[str] = None

    def __init__(
        self,
        model_id: str,
        api_key: str,
        model_type: Optional[OpenAIModelTypes],
        org_id: Optional[str] = None,
        log: Optional[Logger] = None,
    ) -> None:
        """
        Initialize an OpenAITextCompletion service.

        Arguments:
            model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            api_key {str} -- OpenAI API key, see
                https://platform.openai.com/account/api-keys
            org_id {Optional[str]} -- OpenAI organization ID.
                This is usually optional unless your
                account belongs to multiple organizations.
            log {Optional[Logger]} -- The logger instance to use. (Optional)
        """
        super().__init__(
            model_id=model_id,
            api_key=api_key,
            org_id=org_id,
            api_type="open_ai",
            log=log,
            model_type=model_type,
        )

    def to_dict(self) -> Dict[str, str]:
        """
        Create a dict of the service settings.
        """
        return self.dict(
            exclude={
                "prompt_tokens",
                "completion_tokens",
                "total_tokens",
                "api_type",
                "model_type",
            },
            by_alias=True,
            exclude_none=True,
        )

    def get_model_args(self) -> Dict[str, Any]:
        model_args = {
            "model": self.model_id,
            "api_type": "open_ai",
        }
        if self.org_id:
            model_args["organization"] = self.org_id
        return model_args
