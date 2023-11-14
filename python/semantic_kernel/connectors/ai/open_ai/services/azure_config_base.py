# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import TYPE_CHECKING, Any, Dict, Optional

from openai import AsyncAzureOpenAI
from openai.lib.azure import AsyncAzureADTokenProvider

from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import (
    OpenAIHandler,
    OpenAIModelTypes,
)

if TYPE_CHECKING:
    pass


class AzureOpenAIConfigBase(OpenAIHandler):
    def __init__(
        self,
        deployment_name: str,
        endpoint: str,
        model_type: Optional[OpenAIModelTypes],
        api_version: str = "2022-12-01",
        api_key: Optional[str] = None,
        ad_token: Optional[str] = None,
        ad_token_provider: Optional[AsyncAzureADTokenProvider] = None,
        log: Optional[Logger] = None,
    ) -> None:
        if api_key:
            client = AsyncAzureOpenAI(
                azure_endpoint=endpoint,
                azure_deployment=deployment_name,
                api_key=api_key,
                api_version=api_version,
            )
        elif ad_token:
            client = AsyncAzureOpenAI(
                azure_endpoint=endpoint,
                azure_deployment=deployment_name,
                api_version=api_version,
                ad_token=ad_token,
            )
        else:
            client = AsyncAzureOpenAI(
                azure_endpoint=endpoint,
                azure_deployment=deployment_name,
                api_version=api_version,
                ad_token_provider=ad_token_provider,
            )
        super().__init__(
            model_id=deployment_name,
            client=client,
            log=log,
            model_type=model_type,
        )

    def to_dict(self) -> Dict[str, str]:
        return self.dict(
            exclude={
                "prompt_tokens",
                "completion_tokens",
                "total_tokens",
                "api_type",
                "org_id",
                "model_type",
            },
            by_alias=True,
            exclude_none=True,
        )

    def get_model_args(self) -> Dict[str, Any]:
        return {"model": self.model_id}
