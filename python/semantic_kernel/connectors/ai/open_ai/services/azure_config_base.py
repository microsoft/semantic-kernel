# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import Any, Awaitable, Callable, Dict, Mapping, Optional, Union

from openai import AsyncAzureOpenAI
from pydantic import validate_call

from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.open_ai.const import DEFAULT_AZURE_API_VERSION
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import (
    OpenAIHandler,
    OpenAIModelTypes,
)
from semantic_kernel.sk_pydantic import HttpsUrl


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
        api_key: Optional[str] = None,
        ad_token: Optional[str] = None,
        ad_token_provider: Optional[Callable[[], Union[str, Awaitable[str]]]] = None,
        default_headers: Mapping[str, str] | None = None,
        log: Optional[Logger] = None,
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
            ad_token_provider {Optional[Callable[[], Union[str, Awaitable[str]]]]} -- A callable or coroutine function providing Azure AD tokens. (Optional)
            default_headers {Mapping[str, str] | None} -- Default headers for HTTP requests. (Optional)
            log {Optional[Logger]} -- Logger instance for logging purposes. (Optional)
            async_client {Optional[AsyncAzureOpenAI]} -- An existing client to use. (Optional)

        The `validate_call` decorator is used with a configuration that allows arbitrary types. This is necessary for types like `HttpsUrl` and `OpenAIModelTypes`.
        """
        # TODO: add SK user-agent here

        # Perform some error checking upfront as we now allow users to pass in
        # a custom AsyncAzureOpenAI client
        if not api_key and not ad_token and not ad_token_provider:
            raise AIException(
                AIException.ErrorCodes.InvalidConfiguration,
                "Please provide either api_key, ad_token or ad_token_provider",
            )
        if not async_client:
            if base_url:
                async_client = AsyncAzureOpenAI(
                    base_url=base_url,
                    api_version=api_version,
                    api_key=api_key,
                    azure_ad_token=ad_token,
                    azure_ad_token_provider=ad_token_provider,
                    default_headers=default_headers,
                )
            else:
                if not endpoint:
                    raise AIException(
                        AIException.ErrorCodes.InvalidConfiguration,
                        "Please provide either base_url or endpoint",
                    )
                async_client = AsyncAzureOpenAI(
                    azure_endpoint=endpoint,
                    azure_deployment=deployment_name,
                    api_version=api_version,
                    api_key=api_key,
                    azure_ad_token=ad_token,
                    azure_ad_token_provider=ad_token_provider,
                    default_headers=default_headers,
                )

        super().__init__(
            ai_model_id=deployment_name,
            log=log,
            client=async_client,
            ai_model_type=ai_model_type,
        )

    def to_dict(self) -> Dict[str, str]:
        client_settings = {
            "deployment_name": self.ai_model_id,
            "base_url": self.client.base_url,
            "api_version": self.client._custom_query["api-version"],
            "api_key": self.client.api_key,
            "ad_token": self.client._azure_ad_token,
            "ad_token_provider": self.client._azure_ad_token_provider,
            "default_headers": self.client.default_headers,
        }
        base = self.model_dump(
            exclude={
                "prompt_tokens",
                "completion_tokens",
                "total_tokens",
                "api_type",
                "org_id",
                "ai_model_type",
                "client",
            },
            by_alias=True,
            exclude_none=True,
        )
        base.update(client_settings)
        return base

    def get_model_args(self) -> Dict[str, Any]:
        return {"model": self.ai_model_id}
