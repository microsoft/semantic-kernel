# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Awaitable, Callable, Dict, Mapping, Optional, Union

from openai import AsyncAzureOpenAI
from pydantic import validate_call

from semantic_kernel.connectors.ai.open_ai.const import (
    DEFAULT_AZURE_API_VERSION,
    USER_AGENT,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import (
    OpenAIHandler,
    OpenAIModelTypes,
)
from semantic_kernel.connectors.telemetry import APP_INFO, prepend_semantic_kernel_to_user_agent
from semantic_kernel.exceptions import ServiceInitializationError
from semantic_kernel.kernel_pydantic import HttpsUrl

logger: logging.Logger = logging.getLogger(__name__)


class AzureOpenAIConfigBase(OpenAIHandler):
    """Internal class for configuring a connection to an Azure OpenAI service."""

    @validate_call(config=dict(arbitrary_types_allowed=True))
    def __init__(
        self,
        deployment_name: str,
        ai_model_type: OpenAIModelTypes,
        endpoint: Optional[HttpsUrl] = None,
        base_url: Optional[HttpsUrl] = None,
        api_version: str = DEFAULT_AZURE_API_VERSION,
        service_id: Optional[str] = None,
        api_key: Optional[str] = None,
        ad_token: Optional[str] = None,
        ad_token_provider: Optional[Callable[[], Union[str, Awaitable[str]]]] = None,
        default_headers: Union[Mapping[str, str], None] = None,
        async_client: Optional[AsyncAzureOpenAI] = None,
    ) -> None:
        """Internal class for configuring a connection to an Azure OpenAI service.

        Arguments:
            deployment_name {str} -- Name of the deployment.
            ai_model_type {OpenAIModelTypes} -- The type of OpenAI model to deploy.
            endpoint {Optional[HttpsUrl]} -- The specific endpoint URL for the deployment. (Optional)
            base_url {Optional[HttpsUrl]} -- The base URL for Azure services. (Optional)
            api_version {str} -- Azure API version. Defaults to the defined DEFAULT_AZURE_API_VERSION.
            api_key {Optional[str]} -- API key for Azure services. (Optional)
            ad_token {Optional[str]} -- Azure AD token for authentication. (Optional)
            ad_token_provider {Optional[Callable[[], Union[str, Awaitable[str]]]]} -- A callable
                or coroutine function providing Azure AD tokens. (Optional)
            default_headers {Union[Mapping[str, str], None]} -- Default headers for HTTP requests. (Optional)
            async_client {Optional[AsyncAzureOpenAI]} -- An existing client to use. (Optional)

        The `validate_call` decorator is used with a configuration that allows arbitrary types.
        This is necessary for types like `HttpsUrl` and `OpenAIModelTypes`.
        """
        # Merge APP_INFO into the headers if it exists
        merged_headers = default_headers.copy() if default_headers else {}
        if APP_INFO:
            merged_headers.update(APP_INFO)
            merged_headers = prepend_semantic_kernel_to_user_agent(merged_headers)

        if not async_client:
            if not api_key and not ad_token and not ad_token_provider:
                raise ServiceInitializationError("Please provide either api_key, ad_token or ad_token_provider")
            if base_url:
                async_client = AsyncAzureOpenAI(
                    base_url=str(base_url),
                    api_version=api_version,
                    api_key=api_key,
                    azure_ad_token=ad_token,
                    azure_ad_token_provider=ad_token_provider,
                    default_headers=merged_headers,
                )
            else:
                if not endpoint:
                    raise ServiceInitializationError("Please provide either base_url or endpoint")
                async_client = AsyncAzureOpenAI(
                    azure_endpoint=str(endpoint).rstrip("/"),
                    azure_deployment=deployment_name,
                    api_version=api_version,
                    api_key=api_key,
                    azure_ad_token=ad_token,
                    azure_ad_token_provider=ad_token_provider,
                    default_headers=merged_headers,
                )
        args = {
            "ai_model_id": deployment_name,
            "client": async_client,
            "ai_model_type": ai_model_type,
        }
        if service_id:
            args["service_id"] = service_id
        super().__init__(**args)

    def to_dict(self) -> Dict[str, str]:
        client_settings = {
            "base_url": str(self.client.base_url),
            "api_version": self.client._custom_query["api-version"],
            "api_key": self.client.api_key,
            "ad_token": self.client._azure_ad_token,
            "ad_token_provider": self.client._azure_ad_token_provider,
            "default_headers": {k: v for k, v in self.client.default_headers.items() if k != USER_AGENT},
        }
        base = self.model_dump(
            exclude={
                "prompt_tokens",
                "completion_tokens",
                "total_tokens",
                "api_type",
                "org_id",
                "ai_model_type",
                "service_id",
                "client",
            },
            by_alias=True,
            exclude_none=True,
        )
        base.update(client_settings)
        return base
