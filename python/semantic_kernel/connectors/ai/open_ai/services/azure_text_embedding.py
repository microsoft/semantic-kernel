# Copyright (c) Microsoft. All rights reserved.


import logging
from typing import Mapping

from openai import AsyncAzureOpenAI
from openai.lib.azure import AsyncAzureADTokenProvider
from pydantic import ValidationError

from semantic_kernel.connectors.ai.open_ai.services.azure_config_base import (
    AzureOpenAIConfigBase,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import (
    OpenAIModelTypes,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_embedding_base import (
    OpenAITextEmbeddingBase,
)
from semantic_kernel.connectors.ai.settings.azure_open_ai_settings import AzureOpenAISettings
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError
from semantic_kernel.kernel_pydantic import HttpsUrl

logger: logging.Logger = logging.getLogger(__name__)


class AzureTextEmbedding(AzureOpenAIConfigBase, OpenAITextEmbeddingBase):
    """Azure Text Embedding class."""

    def __init__(
        self,
        service_id: str | None = None,
        ad_token: str | None = None,
        ad_token_provider: AsyncAzureADTokenProvider | None = None,
        default_headers: Mapping[str, str] | None = None,
        async_client: AsyncAzureOpenAI | None = None,
        use_env_settings_file: bool = False,
    ) -> None:
        """
        Initialize an AzureTextEmbedding service.

        :param service_id: The service ID. (Optional)
        :param ad_token : The Azure AD token for authentication. (Optional)
        :param ad_auth: Whether to use Azure Active Directory authentication.
            (Optional) The default value is False.
        :param default_headers: The default headers mapping of string keys to
            string values for HTTP requests. (Optional)
        :param async_client: An existing client to use. (Optional)
        :param use_env_settings_file: Use the environment settings file as a
            fallback to environment variables. (Optional)

        """
        try:
            azure_openai_settings = AzureOpenAISettings(use_env_settings_file=use_env_settings_file)
        except ValidationError as e:
            logger.error(f"Error loading Azure OpenAI settings: {e}")
            raise ServiceInitializationError("Error loading Azure OpenAI settings") from e
        base_url = azure_openai_settings.base_url
        endpoint = azure_openai_settings.endpoint
        deployment_name = azure_openai_settings.embedding_deployment_name
        api_version = azure_openai_settings.api_version
        api_key = azure_openai_settings.api_key.get_secret_value()

        if not base_url and not endpoint:
            raise ServiceInitializationError("At least one of base_url or endpoint must be provided.")

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
                should contains keys: deployment_name, endpoint, api_key
                and optionally: api_version, ad_auth
        """
        return AzureTextEmbedding(
            service_id=settings.get("service_id"),
            ad_token=settings.get("ad_token"),
            ad_token_provider=settings.get("ad_token_provider"),
            default_headers=settings.get("default_headers"),
            use_env_settings_file=settings.get("use_env_settings_file", False),
        )
