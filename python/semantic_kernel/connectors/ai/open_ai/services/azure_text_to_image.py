# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Mapping
from typing import Any, TypeVar

from openai import AsyncAzureOpenAI
from openai.lib.azure import AsyncAzureADTokenProvider
from pydantic import ValidationError

from semantic_kernel.connectors.ai.open_ai.services.azure_config_base import AzureOpenAIConfigBase
from semantic_kernel.connectors.ai.open_ai.services.open_ai_model_types import OpenAIModelTypes
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_to_image_base import OpenAITextToImageBase
from semantic_kernel.connectors.ai.open_ai.settings.azure_open_ai_settings import AzureOpenAISettings
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError

T_ = TypeVar("T_", bound="AzureTextToImage")


class AzureTextToImage(AzureOpenAIConfigBase, OpenAITextToImageBase):
    """Azure Text to Image service."""

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
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize an AzureTextToImage service.

        Args:
            service_id: The service ID. (Optional)
            api_key: The optional api key. If provided, will override the value in the
                    env vars or .env file.
            deployment_name: The optional deployment. If provided, will override the value
                (text_to_image_deployment_name) in the env vars or .env file.
            endpoint: The optional deployment endpoint. If provided will override the value
                in the env vars or .env file.
            base_url: The optional deployment base_url. If provided will override the value
                in the env vars or .env file.
            api_version: The optional deployment api version. If provided will override the value
                in the env vars or .env file.
            ad_token: The Azure AD token for authentication. (Optional)
            ad_token_provider: Azure AD Token provider. (Optional)
            ad_auth: Whether to use Azure Active Directory authentication.
                (Optional) The default value is False.
            default_headers: The default headers mapping of string keys to
                    string values for HTTP requests. (Optional)
            async_client: An existing client to use. (Optional)
            env_file_path: Use the environment settings file as a fallback to
                environment variables. (Optional)
            env_file_encoding: The encoding of the environment settings file. (Optional)
        """
        try:
            azure_openai_settings = AzureOpenAISettings.create(
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
                api_key=api_key,
                text_to_image_deployment_name=deployment_name,
                endpoint=endpoint,
                base_url=base_url,
                api_version=api_version,
            )
        except ValidationError as exc:
            raise ServiceInitializationError(f"Invalid settings: {exc}") from exc
        if not azure_openai_settings.text_to_image_deployment_name:
            raise ServiceInitializationError("The Azure OpenAI text to image deployment name is required.")

        super().__init__(
            deployment_name=azure_openai_settings.text_to_image_deployment_name,
            endpoint=azure_openai_settings.endpoint,
            base_url=azure_openai_settings.base_url,
            api_version=azure_openai_settings.api_version,
            service_id=service_id,
            api_key=azure_openai_settings.api_key.get_secret_value() if azure_openai_settings.api_key else None,
            ad_token=ad_token,
            ad_token_provider=ad_token_provider,
            default_headers=default_headers,
            ai_model_type=OpenAIModelTypes.IMAGE,
            client=async_client,
        )

    @classmethod
    def from_dict(cls: type[T_], settings: dict[str, Any]) -> T_:
        """Initialize an Azure OpenAI service from a dictionary of settings.

        Args:
            settings: A dictionary of settings for the service.
                should contain keys: deployment_name, endpoint, api_key
                and optionally: api_version, ad_auth
        """
        return cls(
            service_id=settings.get("service_id"),
            api_key=settings.get("api_key"),
            deployment_name=settings.get("deployment_name"),
            endpoint=settings.get("endpoint"),
            base_url=settings.get("base_url"),
            api_version=settings.get("api_version"),
            ad_token=settings.get("ad_token"),
            ad_token_provider=settings.get("ad_token_provider"),
            default_headers=settings.get("default_headers"),
            env_file_path=settings.get("env_file_path"),
        )
