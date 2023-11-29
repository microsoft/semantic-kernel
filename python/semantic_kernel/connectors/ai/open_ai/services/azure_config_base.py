# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import Any, Awaitable, Callable, Dict, Optional, Union

from openai import AsyncAzureOpenAI
from pydantic import validate_arguments

from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.open_ai.const import DEFAULT_AZURE_API_VERSION
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import (
    OpenAIHandler,
    OpenAIModelTypes,
)
from semantic_kernel.sk_pydantic import HttpsUrl


class AzureOpenAIConfigBase(OpenAIHandler):
    """Internal class for configuring a connection to an Azure OpenAI service."""

    @validate_arguments(config=dict(arbitrary_types_allowed=True))
    def __init__(
        self,
        deployment_name: str,
        model_type: OpenAIModelTypes,
        endpoint: Optional[HttpsUrl] = None,
        base_url: Optional[HttpsUrl] = None,
        api_version: str = DEFAULT_AZURE_API_VERSION,
        api_key: Optional[str] = None,
        ad_token: Optional[str] = None,
        ad_token_provider: Optional[Callable[[], Union[str, Awaitable[str]]]] = None,
        log: Optional[Logger] = None,
    ) -> None:
        # TODO: add SK user-agent here
        if not api_key and not ad_token and not ad_token_provider:
            raise AIException(
                AIException.ErrorCodes.InvalidConfiguration,
                "Please provide either api_key, ad_token or ad_token_provider",
            )
        if not base_url and not endpoint:
            raise AIException(
                AIException.ErrorCodes.InvalidConfiguration,
                "Please provide either base_url or endpoint",
            )
        if base_url:
            client = AsyncAzureOpenAI(
                base_url=base_url,
                api_version=api_version,
                api_key=api_key,
                azure_ad_token=ad_token,
                azure_ad_token_provider=ad_token_provider,
            )
        else:
            client = AsyncAzureOpenAI(
                azure_endpoint=endpoint,
                azure_deployment=deployment_name,
                api_version=api_version,
                api_key=api_key,
                azure_ad_token=ad_token,
                azure_ad_token_provider=ad_token_provider,
            )
        super().__init__(
            model_id=deployment_name,
            log=log,
            client=client,
            model_type=model_type,
        )

    def to_dict(self) -> Dict[str, str]:
        client_settings = {
            "base_url": self.client.base_url,
            "api_version": self.client._custom_query["api-version"],
            "api_key": self.client.api_key,
            "ad_token": self.client._azure_ad_token,
            "ad_token_provider": self.client._azure_ad_token_provider,
        }
        base = self.dict(
            exclude={
                "prompt_tokens",
                "completion_tokens",
                "total_tokens",
                "api_type",
                "org_id",
                "model_type",
                "client",
            },
            by_alias=True,
            exclude_none=True,
        )
        base.update(client_settings)
        return base

    def get_model_args(self) -> Dict[str, Any]:
        return {"model": self.model_id}
