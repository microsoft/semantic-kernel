# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import Any, Dict, Optional

from openai import AsyncOpenAI
from pydantic import Field, validate_call

from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import (
    OpenAIHandler,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_model_types import (
    OpenAIModelTypes,
)


class OpenAIConfigBase(OpenAIHandler):
    @validate_call(config=dict(arbitrary_types_allowed=True))
    def __init__(
        self,
        ai_model_id: str = Field(min_length=1),
        api_key: str = Field(min_length=1),
        ai_model_type: Optional[OpenAIModelTypes] = OpenAIModelTypes.CHAT,
        org_id: Optional[str] = None,
        log: Optional[Logger] = None,
    ) -> None:
        # TODO: add SK user-agent here
        client = AsyncOpenAI(api_key=api_key, organization=org_id)
        super().__init__(
            ai_model_id=ai_model_id,
            client=client,
            log=log,
            ai_model_type=ai_model_type,
        )

    def to_dict(self) -> Dict[str, str]:
        """
        Create a dict of the service settings.
        """
        client_settings = {
            "api_key": self.client.api_key,
        }
        if self.client.organization:
            client_settings["org_id"] = self.client.organization
        base = self.model_dump(
            exclude={
                "prompt_tokens",
                "completion_tokens",
                "total_tokens",
                "api_type",
                "ai_model_type",
                "client",
            },
            by_alias=True,
            exclude_none=True,
        )
        base.update(client_settings)
        return base

    def get_model_args(self) -> Dict[str, Any]:
        return {
            "model": self.ai_model_id,
        }
