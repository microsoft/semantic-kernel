# Copyright (c) Microsoft. All rights reserved.

import logging
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
from collections.abc import Mapping
from typing import Any
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
from collections.abc import Mapping
from typing import Any
=======
<<<<<<< div
=======
>>>>>>> main
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
from collections.abc import Mapping
from typing import Any
=======
from typing import Dict, Mapping, Optional, overload
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head

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
from semantic_kernel.connectors.ai.open_ai.settings.azure_open_ai_settings import (
    AzureOpenAISettings,
)
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError
from semantic_kernel.utils.experimental_decorator import experimental_class
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream

logger: logging.Logger = logging.getLogger(__name__)

=======

logger: logging.Logger = logging.getLogger(__name__)
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
>>>>>>> head

=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======

<<<<<<< div
<<<<<<< div
=======
<<<<<<< head
=======
<<<<<<< main
=======

>>>>>>> Stashed changes
=======
<<<<<<< main
=======

>>>>>>> Stashed changes
>>>>>>> head
logger: logging.Logger = logging.getLogger(__name__)
>>>>>>> origin/main

logger: logging.Logger = logging.getLogger(__name__)

<<<<<<< main

=======
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head
@experimental_class
class AzureTextEmbedding(AzureOpenAIConfigBase, OpenAITextEmbeddingBase):
    """Azure Text Embedding class."""

    def __init__(
        self,
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
>>>>>>> Stashed changes
>>>>>>> head
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
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
    ) -> None:
        """Initialize an AzureTextEmbedding service.

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
        async_client (Optional[AsyncAzureOpenAI]): An existing client to use. (Optional)
        env_file_path (str | None): Use the environment settings file as a fallback to
            environment variables. (Optional)
        """
        try:
            azure_openai_settings = AzureOpenAISettings.create(
                env_file_path=env_file_path,
                api_key=api_key,
                embedding_deployment_name=deployment_name,
                endpoint=endpoint,
                base_url=base_url,
                api_version=api_version,
            )
        except ValidationError as exc:
            raise ServiceInitializationError(f"Invalid settings: {exc}") from exc
        if not azure_openai_settings.embedding_deployment_name:
            raise ServiceInitializationError(
                "The Azure OpenAI embedding deployment name is required."
            )

        # If the api_key is none, and the ad_token is none, and the ad_token_provider is none,
        # then we will attempt to get the ad_token using the default endpoint specified in the Azure OpenAI settings.
        if api_key is None and ad_token_provider is None and azure_openai_settings.token_endpoint and ad_token is None:
            ad_token = azure_openai_settings.get_azure_openai_auth_token(
                token_endpoint=azure_openai_settings.token_endpoint
            )

        super().__init__(
            deployment_name=azure_openai_settings.embedding_deployment_name,
            endpoint=azure_openai_settings.endpoint,
            base_url=azure_openai_settings.base_url,
            api_version=azure_openai_settings.api_version,
            service_id=service_id,
            api_key=(
                azure_openai_settings.api_key.get_secret_value()
                if azure_openai_settings.api_key
                else None
            ),
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
        deployment_name: str,
        async_client: AsyncAzureOpenAI,
        service_id: Optional[str] = None,
>>>>>>> ms/small_fixes
    ) -> None:
        """Initialize an AzureTextEmbedding service.

<<<<<<< main
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
        async_client (Optional[AsyncAzureOpenAI]): An existing client to use. (Optional)
        env_file_path (str | None): Use the environment settings file as a fallback to
            environment variables. (Optional)
=======
        Arguments:
            deployment_name: The name of the Azure deployment. This value
                will correspond to the custom name you chose for your deployment
                when you deployed a model. This value can be found under
                Resource Management > Deployments in the Azure portal or, alternatively,
                under Management > Deployments in Azure OpenAI Studio.
            async_client {AsyncAzureOpenAI} -- An existing client to use.
        """

    def __init__(
        self,
        deployment_name: str,
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
        deployment_name: str,
        async_client: AsyncAzureOpenAI,
        service_id: Optional[str] = None,
>>>>>>> ms/small_fixes
    ) -> None:
        """Initialize an AzureTextEmbedding service.

<<<<<<< main
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
        async_client (Optional[AsyncAzureOpenAI]): An existing client to use. (Optional)
        env_file_path (str | None): Use the environment settings file as a fallback to
            environment variables. (Optional)
=======
        Arguments:
            deployment_name: The name of the Azure deployment. This value
                will correspond to the custom name you chose for your deployment
                when you deployed a model. This value can be found under
                Resource Management > Deployments in the Azure portal or, alternatively,
                under Management > Deployments in Azure OpenAI Studio.
            async_client {AsyncAzureOpenAI} -- An existing client to use.
        """

    def __init__(
        self,
        deployment_name: str,
<<<<<<< div
=======
=======
        deployment_name: str,
        async_client: AsyncAzureOpenAI,
        service_id: Optional[str] = None,
>>>>>>> ms/small_fixes
    ) -> None:
        """Initialize an AzureTextEmbedding service.

<<<<<<< main
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
        async_client (Optional[AsyncAzureOpenAI]): An existing client to use. (Optional)
        env_file_path (str | None): Use the environment settings file as a fallback to
            environment variables. (Optional)
=======
        Arguments:
            deployment_name: The name of the Azure deployment. This value
                will correspond to the custom name you chose for your deployment
                when you deployed a model. This value can be found under
                Resource Management > Deployments in the Azure portal or, alternatively,
                under Management > Deployments in Azure OpenAI Studio.
            async_client {AsyncAzureOpenAI} -- An existing client to use.
        """

    def __init__(
        self,
        deployment_name: str,
>>>>>>> main
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
        endpoint: Optional[str] = None,
        api_version: str = DEFAULT_AZURE_API_VERSION,
        service_id: Optional[str] = None,
        api_key: Optional[str] = None,
        ad_token: Optional[str] = None,
        ad_token_provider: Optional[AsyncAzureADTokenProvider] = None,
        default_headers: Optional[Mapping[str, str]] = None,
        async_client: Optional[AsyncAzureOpenAI] = None,
    ) -> None:
>>>>>>> ms/small_fixes
        """
        try:
            azure_openai_settings = AzureOpenAISettings.create(
                env_file_path=env_file_path,
                api_key=api_key,
                embedding_deployment_name=deployment_name,
                endpoint=endpoint,
                base_url=base_url,
                api_version=api_version,
            )
        except ValidationError as exc:
            raise ServiceInitializationError(f"Invalid settings: {exc}") from exc
        if not azure_openai_settings.embedding_deployment_name:
            raise ServiceInitializationError(
                "The Azure OpenAI embedding deployment name is required."
            )

<<<<<<< main
        # If the api_key is none, and the ad_token is none, and the ad_token_provider is none,
        # then we will attempt to get the ad_token using the default endpoint specified in the Azure OpenAI settings.
        if (
            azure_openai_settings.api_key is None
            and ad_token_provider is None
            and azure_openai_settings.token_endpoint
            and ad_token is None
            and async_client is None
        ):
            ad_token = azure_openai_settings.get_azure_openai_auth_token(
                token_endpoint=azure_openai_settings.token_endpoint
            )

        if not azure_openai_settings.api_key and not ad_token and not ad_token_provider and not async_client:
            raise ServiceInitializationError(
                "Please provide either api_key, ad_token, ad_token_provider, or a custom client"
            )

        super().__init__(
            deployment_name=azure_openai_settings.embedding_deployment_name,
            endpoint=azure_openai_settings.endpoint,
            base_url=azure_openai_settings.base_url,
            api_version=azure_openai_settings.api_version,
            service_id=service_id,
            api_key=(
                azure_openai_settings.api_key.get_secret_value()
                if azure_openai_settings.api_key
                else None
            ),
=======
        :param deployment_name: The name of the Azure deployment. This value
            will correspond to the custom name you chose for your deployment
            when you deployed a model. This value can be found under
            Resource Management > Deployments in the Azure portal or, alternatively,
            under Management > Deployments in Azure OpenAI Studio.
        :param endpoint: The endpoint of the Azure deployment. This value
            can be found in the Keys & Endpoint section when examining
            your resource from the Azure portal.
        :param api_version: The API version to use. (Optional)
            The default value is "2023-05-15".
        :param api_key: The API key for the Azure deployment. This value can be
            found in the Keys & Endpoint section when examining your resource in
            the Azure portal. You can use either KEY1 or KEY2.
        :param ad_token : The Azure AD token for authentication. (Optional)
        :param ad_auth: Whether to use Azure Active Directory authentication.
            (Optional) The default value is False.
        :param default_headers: The default headers mapping of string keys to
            string values for HTTP requests. (Optional)
        :param async_client: An existing client to use. (Optional)

        """
        super().__init__(
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_version=api_version,
            service_id=service_id,
            api_key=api_key,
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
            ad_token=ad_token,
            ad_token_provider=ad_token_provider,
            default_headers=default_headers,
            ai_model_type=OpenAIModelTypes.EMBEDDING,
            client=async_client,
        )

    @classmethod
    def from_dict(cls, settings: dict[str, Any]) -> "AzureTextEmbedding":
        """Initialize an Azure OpenAI service from a dictionary of settings.

        Args:
            settings: A dictionary of settings for the service.
                should contain keys: deployment_name, endpoint, api_key
                and optionally: api_version, ad_auth
        """
        return AzureTextEmbedding(
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
>>>>>>> Stashed changes
>>>>>>> head
            service_id=settings.get("service_id"),
            api_key=settings.get("api_key"),
            deployment_name=settings.get("deployment_name"),
            endpoint=settings.get("endpoint"),
            base_url=settings.get("base_url"),
            api_version=settings.get("api_version"),
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> head
=======
>>>>>>> origin/main
=======
=======
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
            deployment_name=settings["deployment_name"],
            endpoint=settings["endpoint"],
            api_key=settings["api_key"],
            api_version=settings.get("api_version", DEFAULT_AZURE_API_VERSION),
            service_id=settings.get("service_id"),
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
            ad_token=settings.get("ad_token"),
            ad_token_provider=settings.get("ad_token_provider"),
            default_headers=settings.get("default_headers"),
            env_file_path=settings.get("env_file_path"),
        )
