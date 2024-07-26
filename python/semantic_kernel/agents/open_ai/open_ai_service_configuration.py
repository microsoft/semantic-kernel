# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Awaitable, Callable

from openai import AsyncAzureOpenAI, AsyncOpenAI
from pydantic import ValidationError

from semantic_kernel.connectors.ai.open_ai.settings.azure_open_ai_settings import AzureOpenAISettings
from semantic_kernel.connectors.ai.open_ai.settings.open_ai_settings import OpenAISettings
from semantic_kernel.exceptions.agent_exceptions import AgentInitializationError
from semantic_kernel.kernel_pydantic import HttpsUrl, KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class OpenAIServiceConfiguration(KernelBaseModel):
    service_id: str
    ai_model_id: str | None = None
    api_key: str | None = None
    org_id: str | None = None
    openai_client: AsyncOpenAI | None = None
    default_headers: dict[str, str] | None = None

    @classmethod
    def create(
        cls,
        service_id: str,
        ai_model_id: str | None = None,
        api_key: str | None = None,
        org_id: str | None = None,
        client: AsyncOpenAI | None = None,
        default_headers: dict[str, str] | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> "OpenAIServiceConfiguration":
        """Create an OpenAI service configuration."""
        try:
            openai_settings = OpenAISettings.create(
                api_key=api_key,
                org_id=org_id,
                chat_model_id=ai_model_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise AgentInitializationError("Failed to create OpenAI settings.", ex) from ex

        if not client and not openai_settings.api_key:
            raise AgentInitializationError("The OpenAI API key is required.")
        if not openai_settings.chat_model_id:
            raise AgentInitializationError("The OpenAI model ID is required.")

        return cls(
            service_id=service_id,
            api_key=openai_settings.api_key.get_secret_value() if openai_settings.api_key else None,
            ai_model_id=openai_settings.chat_model_id,
            org_id=openai_settings.org_id,
            openai_client=client,
            default_headers=default_headers,
        )


@experimental_class
class AzureOpenAIServiceConfiguration(OpenAIServiceConfiguration):
    endpoint: HttpsUrl | None = None
    ad_token: str | None = None
    ad_token_provider: Callable[[], str | Awaitable[str]] | None = None
    azure_openai_client: AsyncAzureOpenAI | None = None
    api_version: str | None = None
    deployment_name: str | None = None

    @classmethod
    def create(  # type: ignore
        cls,
        service_id: str,
        api_key: str | None = None,
        org_id: str | None = None,
        endpoint: str | None = None,
        deployment_name: str | None = None,
        api_version: str | None = None,
        ad_token: str | None = None,
        ad_token_provider: Callable[[], str | Awaitable[str]] | None = None,
        client: AsyncAzureOpenAI | None = None,
        default_headers: dict[str, str] | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> "AzureOpenAIServiceConfiguration":
        """Create an Azure OpenAI service configuration."""
        try:
            azure_openai_settings = AzureOpenAISettings.create(
                api_key=api_key,
                endpoint=endpoint,
                chat_deployment_name=deployment_name,
                api_version=api_version,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise AgentInitializationError("Failed to create Azure OpenAI settings.", ex) from ex

        if not azure_openai_settings.chat_deployment_name:
            raise AgentInitializationError("chat_deployment_name is required.")

        if not azure_openai_settings.api_key and not ad_token and not ad_token_provider:
            raise AgentInitializationError("Please provide either api_key, ad_token or ad_token_provider")

        return cls(
            service_id=service_id,
            api_key=azure_openai_settings.api_key.get_secret_value() if azure_openai_settings.api_key else None,
            ai_model_id=azure_openai_settings.chat_deployment_name,
            org_id=org_id,
            endpoint=azure_openai_settings.endpoint,
            deployment_name=azure_openai_settings.chat_deployment_name,
            api_version=azure_openai_settings.api_version,
            ad_token=ad_token,
            ad_token_provider=ad_token_provider,
            azure_openai_client=client,
            default_headers=default_headers,
        )
