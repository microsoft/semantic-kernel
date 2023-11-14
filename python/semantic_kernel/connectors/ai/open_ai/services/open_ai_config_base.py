# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import Any, Dict, Optional

from openai import AsyncOpenAI

from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import (
    OpenAIHandler,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_model_types import (
    OpenAIModelTypes,
)


class OpenAIConfigBase(OpenAIHandler):
    def __init__(
        self,
        model_id: str,
        api_key: str,
        model_type: Optional[OpenAIModelTypes],
        org_id: Optional[str] = None,
        log: Optional[Logger] = None,
    ) -> None:
        client = AsyncOpenAI(api_key=api_key, organization=org_id)
        super().__init__(
            model_id=model_id,
            client=client,
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
        return {
            "model": self.model_id,
        }
