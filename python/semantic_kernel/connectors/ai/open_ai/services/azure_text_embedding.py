# Copyright (c) Microsoft. All rights reserved.


import logging
from collections.abc import Mapping

from openai import AsyncAzureOpenAI
from openai.lib.azure import AsyncAzureADTokenProvider
from pydantic import ValidationError

from semantic_kernel.connectors.ai.open_ai.const import DEFAULT_AZURE_API_VERSION
from semantic_kernel.connectors.ai.open_ai.services.azure_config_base import (
    AzureOpenAIConfigBase,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import (
    OpenAIModelTypes,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_embedding_base import (
    OpenAITextEmbeddingBase,
)
from semantic_kernel.connectors.ai.open_ai.settings.azure_open_ai_settings import AzureOpenAISettings
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError
from semantic_kernel.kernel_pydantic import HttpsUrl
from semantic_kernel.utils.experimental_decorator import experimental_class

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class AzureTextEmbedding(AzureOpenAIConfigBase, OpenAITextEmbeddingBase):
    """Azure Text Embedding class."""

    def __init__(
        self,
        service_id: str | None = None,
        api_key: str | None = None,
        deployment_name: str | None = None,
        endpoint: str | None = None,
        base_url: str | None = None,
        api_version: str | None = None,
        ad_token: str | None = None,
        ad_token_provider: AsyncAzureADTokenProvider | None = None,
        default_headers: Mapping[str, str] | None = None,
        async_client: AsyncAzureOpenAI | None = None,
        env_file_path: str | None = None,
    ) -> None:
        """
        Initialize an AzureTextEmbedding service.

        service_id: The service ID. (Optional)
        api_key  {str | None}: The optional api key. If provided, will override the value in the
                env vars or .env file.
        deployment_name  {str | None}: The optional deployment. If provided, will override the value
            (text_deployment_name) in the env vars or .env file.
        endpoint {str | None}: The optional deployment endpoint. If provided will override the value
            in the env vars or .env file.
        base_url {str | None}: The optional deployment base_url. If provided will override the value
            in the env vars or .env file.
        api_version {str | None}: The optional deployment api version. If provided will override the value
            in the env vars or .env file.
        ad_token {str | None}: The Azure AD token for authentication. (Optional)
        ad_auth {AsyncAzureADTokenProvider | None}: Whether to use Azure Active Directory authentication.
            (Optional) The default value is False.
        default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
        async_client {Optional[AsyncAzureOpenAI]} -- An existing client to use. (Optional)
        env_file_path {str | None} -- Use the environment settings file as a fallback to
            environment variables. (Optional)
        """
        azure_openai_settings = None
        try:
            azure_openai_settings = AzureOpenAISettings.create(env_file_path=env_file_path)
        except ValidationError as e:
            logger.warning(f"Failed to load AzureOpenAI pydantic settings: {e}")

        base_url = base_url or (
            str(azure_openai_settings.base_url) if azure_openai_settings and azure_openai_settings.base_url else None
        )
        endpoint = endpoint or (
            str(azure_openai_settings.endpoint) if azure_openai_settings and azure_openai_settings.endpoint else None
        )
        deployment_name = deployment_name or (
            azure_openai_settings.embedding_deployment_name if azure_openai_settings else None
        )
        api_version = api_version or (azure_openai_settings.api_version if azure_openai_settings else None)
        api_key = api_key or (
            azure_openai_settings.api_key.get_secret_value()
            if azure_openai_settings and azure_openai_settings.api_key
            else None
        )

        if api_version is None:
            api_version = DEFAULT_AZURE_API_VERSION

        if not base_url and not endpoint:
            raise ServiceInitializationError("At least one of base_url or endpoint must be provided.")

        if base_url and isinstance(base_url, str):
            base_url = HttpsUrl(base_url)
        if endpoint and deployment_name:
            base_url = HttpsUrl(f"{str(endpoint).rstrip('/')}/openai/deployments/{deployment_name}")

        super().__init__(
            deployment_name=deployment_name,
            endpoint=endpoint if not isinstance(endpoint, str) else HttpsUrl(endpoint),
            base_url=base_url,
            api_version=api_version,
            service_id=service_id,
            api_key=api_key,
            ad_token=ad_token,
            ad_token_provider=ad_token_provider,
            default_headers=default_headers,
            ai_model_type=OpenAIModelTypes.EMBEDDING,
            async_client=async_client,
        )

    @classmethod
    def from_dict(cls, settings: dict[str, str]) -> "AzureTextEmbedding":
        """
        Initialize an Azure OpenAI service from a dictionary of settings.

        Arguments:
            settings: A dictionary of settings for the service.
                should contain keys: deployment_name, endpoint, api_key
                and optionally: api_version, ad_auth
        """
        return AzureTextEmbedding(
            service_id=settings.get("service_id"),
            api_key=settings.get("api_key", None),
            deployment_name=settings.get("deployment_name", None),
            endpoint=settings.get("endpoint", None),
            base_url=settings.get("base_url", None),
            api_version=settings.get("api_version", None),
            ad_token=settings.get("ad_token"),
            ad_token_provider=settings.get("ad_token_provider"),
            default_headers=settings.get("default_headers"),
            env_file_path=settings.get("env_file_path", None),
        )
