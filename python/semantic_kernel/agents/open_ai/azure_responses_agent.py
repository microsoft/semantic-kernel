# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import Awaitable, Callable
from copy import copy
from typing import TYPE_CHECKING, Any

from openai import AsyncAzureOpenAI
from pydantic import ValidationError

from semantic_kernel.agents import OpenAIResponsesAgent
from semantic_kernel.agents.agent import register_agent_type
from semantic_kernel.connectors.ai.open_ai.settings.azure_open_ai_settings import AzureOpenAISettings
from semantic_kernel.exceptions.agent_exceptions import (
    AgentInitializationException,
)
from semantic_kernel.utils.authentication.entra_id_authentication import get_entra_auth_token
from semantic_kernel.utils.feature_stage_decorator import experimental
from semantic_kernel.utils.telemetry.user_agent import APP_INFO, prepend_semantic_kernel_to_user_agent

if TYPE_CHECKING:
    from semantic_kernel.kernel_pydantic import KernelBaseSettings

logger: logging.Logger = logging.getLogger(__name__)

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

if sys.version < "3.11":
    from typing_extensions import Self  # pragma: no cover
else:
    from typing import Self  # type: ignore # pragma: no cover

if sys.version_info >= (3, 13):
    from warnings import deprecated
else:
    from typing_extensions import deprecated


@experimental
@register_agent_type("azure_responses")
class AzureResponsesAgent(OpenAIResponsesAgent):
    """Azure Responses Agent class.

    Provides the ability to interact with Azure's Responses API.
    """

    @staticmethod
    @deprecated(
        "setup_resources is deprecated. Use AzureResponsesAgent.create_client() instead. This method will be removed by 2025-06-15."  # noqa: E501
    )
    def setup_resources(
        *,
        ad_token: str | None = None,
        ad_token_provider: Callable[[], str | Awaitable[str]] | None = None,
        api_key: str | None = None,
        api_version: str | None = None,
        base_url: str | None = None,
        default_headers: dict[str, str] | None = None,
        deployment_name: str | None = None,
        endpoint: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        token_scope: str | None = None,
        **kwargs: Any,
    ) -> tuple[AsyncAzureOpenAI, str]:
        """A method to create the Azure OpenAI client and the deployment name/model from the provided arguments.

        Any arguments provided will override the values in the environment variables/environment file.

        Args:
            ad_token: The Microsoft Entra (previously Azure AD) token represented as a string
            ad_token_provider: The Microsoft Entra (previously Azure AD) token provider provided as a callback
            api_key: The API key
            api_version: The API version
            base_url: The base URL in the form https://<resource>.azure.openai.com/openai/deployments/<deployment_name>
            default_headers: The default headers to add to the client
            deployment_name: The Responses deployment name
            endpoint: The endpoint in the form https://<resource>.azure.openai.com
            env_file_path: The environment file path
            env_file_encoding: The environment file encoding, defaults to utf-8
            token_scope: The token scope
            kwargs: Additional keyword arguments

        Returns:
            An Azure OpenAI client instance and the configured deployment name (model)
        """
        try:
            azure_openai_settings = AzureOpenAISettings(
                api_key=api_key,
                base_url=base_url,
                endpoint=endpoint,
                responses_deployment_name=deployment_name,
                api_version=api_version,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
                token_endpoint=token_scope,
            )
        except ValidationError as exc:
            raise AgentInitializationException(f"Failed to create Azure OpenAI settings: {exc}") from exc

        if (
            azure_openai_settings.api_key is None
            and ad_token_provider is None
            and ad_token is None
            and azure_openai_settings.token_endpoint
        ):
            ad_token = get_entra_auth_token(azure_openai_settings.token_endpoint)

        # If we still have no credentials, we can't proceed
        if not azure_openai_settings.api_key and not ad_token and not ad_token_provider:
            raise AgentInitializationException(
                "Please provide either an api_key, ad_token or ad_token_provider for authentication."
            )

        merged_headers = dict(copy(default_headers)) if default_headers else {}
        if default_headers:
            merged_headers.update(default_headers)
        if APP_INFO:
            merged_headers.update(APP_INFO)
            merged_headers = prepend_semantic_kernel_to_user_agent(merged_headers)

        if not azure_openai_settings.endpoint:
            raise AgentInitializationException("Please provide an Azure OpenAI endpoint")

        if not azure_openai_settings.responses_deployment_name:
            raise AgentInitializationException("Please provide an Azure OpenAI Responses deployment name")

        client = AsyncAzureOpenAI(
            azure_endpoint=str(azure_openai_settings.endpoint),
            api_version=azure_openai_settings.api_version,
            api_key=azure_openai_settings.api_key.get_secret_value() if azure_openai_settings.api_key else None,
            azure_ad_token=ad_token,
            azure_ad_token_provider=ad_token_provider,
            default_headers=merged_headers,
            **kwargs,
        )

        return client, azure_openai_settings.responses_deployment_name

    @staticmethod
    def create_client(
        *,
        ad_token: str | None = None,
        ad_token_provider: Callable[[], str | Awaitable[str]] | None = None,
        api_key: str | None = None,
        api_version: str | None = None,
        base_url: str | None = None,
        default_headers: dict[str, str] | None = None,
        deployment_name: str | None = None,
        endpoint: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        token_scope: str | None = None,
        **kwargs: Any,
    ) -> AsyncAzureOpenAI:
        """A method to create the Azure OpenAI client.

        Any arguments provided will override the values in the environment variables/environment file.

        Args:
            ad_token: The Microsoft Entra (previously Azure AD) token represented as a string
            ad_token_provider: The Microsoft Entra (previously Azure AD) token provider provided as a callback
            api_key: The API key
            api_version: The API version
            base_url: The base URL in the form https://<resource>.azure.openai.com/openai/deployments/<deployment_name>
            default_headers: The default headers to add to the client
            deployment_name: The Responses deployment name
            endpoint: The endpoint in the form https://<resource>.azure.openai.com
            env_file_path: The environment file path
            env_file_encoding: The environment file encoding, defaults to utf-8
            token_scope: The token scope
            kwargs: Additional keyword arguments

        Returns:
            An Azure OpenAI client instance.
        """
        try:
            azure_openai_settings = AzureOpenAISettings(
                api_key=api_key,
                base_url=base_url,
                endpoint=endpoint,
                responses_deployment_name=deployment_name,
                api_version=api_version,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
                token_endpoint=token_scope,
            )
        except ValidationError as exc:
            raise AgentInitializationException(f"Failed to create Azure OpenAI settings: {exc}") from exc

        if (
            azure_openai_settings.api_key is None
            and ad_token_provider is None
            and ad_token is None
            and azure_openai_settings.token_endpoint
        ):
            ad_token = get_entra_auth_token(azure_openai_settings.token_endpoint)

        # If we still have no credentials, we can't proceed
        if not azure_openai_settings.api_key and not ad_token and not ad_token_provider:
            raise AgentInitializationException(
                "Please provide either an api_key, ad_token or ad_token_provider for authentication."
            )

        merged_headers = dict(copy(default_headers)) if default_headers else {}
        if default_headers:
            merged_headers.update(default_headers)
        if APP_INFO:
            merged_headers.update(APP_INFO)
            merged_headers = prepend_semantic_kernel_to_user_agent(merged_headers)

        if not azure_openai_settings.endpoint:
            raise AgentInitializationException("Please provide an Azure OpenAI endpoint")

        if not azure_openai_settings.responses_deployment_name:
            raise AgentInitializationException("Please provide an Azure OpenAI Responses deployment name")

        return AsyncAzureOpenAI(
            azure_endpoint=str(azure_openai_settings.endpoint),
            api_version=azure_openai_settings.api_version,
            api_key=azure_openai_settings.api_key.get_secret_value() if azure_openai_settings.api_key else None,
            azure_ad_token=ad_token,
            azure_ad_token_provider=ad_token_provider,
            default_headers=merged_headers,
            **kwargs,
        )

    @override
    @classmethod
    def resolve_placeholders(
        cls: type[Self],
        yaml_str: str,
        settings: "KernelBaseSettings | None" = None,
        extras: dict[str, Any] | None = None,
    ) -> str:
        """Substitute ${AzureOpenAI:Key} placeholders with fields from AzureOpenAIAgentSettings and extras."""
        import re

        pattern = re.compile(r"\$\{([^}]+)\}")

        # Build the mapping only if settings is provided and valid
        field_mapping: dict[str, Any] = {}

        if settings is None:
            settings = AzureOpenAISettings()

        if not isinstance(settings, AzureOpenAISettings):
            raise AgentInitializationException(f"Expected AzureOpenAISettings, got {type(settings).__name__}")

        field_mapping.update({
            "ChatModelId": getattr(settings, "responses_deployment_name", None),
            "AgentId": getattr(settings, "agent_id", None),
            "ApiKey": getattr(settings, "api_key", None),
            "ApiVersion": getattr(settings, "api_version", None),
            "BaseUrl": getattr(settings, "base_url", None),
            "Endpoint": getattr(settings, "endpoint", None),
            "TokenEndpoint": getattr(settings, "token_endpoint", None),
        })

        if extras:
            field_mapping.update(extras)

        def replacer(match: re.Match[str]) -> str:
            """Replace the matched placeholder with the corresponding value from field_mapping."""
            full_key = match.group(1)  # for example, AzureOpenAI:ApiKey
            section, _, key = full_key.partition(":")
            if section != "AzureOpenAI":
                return match.group(0)

            # Try short key first (ApiKey), then full (AzureOpenAI:ApiKey)
            return str(field_mapping.get(key) or field_mapping.get(full_key) or match.group(0))

        result = pattern.sub(replacer, yaml_str)

        # Safety check for unresolved placeholders
        unresolved = pattern.findall(result)
        if unresolved:
            raise AgentInitializationException(
                f"Unresolved placeholders in spec: {', '.join(f'${{{key}}}' for key in unresolved)}"
            )

        return result
