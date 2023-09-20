# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import Any, Dict, Optional

from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import (
    OpenAIHandler,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_model_types import (
    OpenAIModelTypes,
)


class OpenAIConfigBase(OpenAIHandler):
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
