# Copyright (c) Microsoft. All rights reserved.
import json
import logging
from collections.abc import Mapping
from copy import deepcopy
from typing import Any, TypeVar
from uuid import uuid4

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
from openai import AsyncAzureOpenAI
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
from openai import AsyncAzureOpenAI
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
from openai import AsyncAzureOpenAI
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
from openai import AsyncAzureOpenAI
=======
>>>>>>> Stashed changes
>>>>>>> head
import json
import logging
import sys
from collections.abc import AsyncGenerator, Mapping
from copy import deepcopy
from typing import Any, TypeVar
from uuid import uuid4

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from openai import AsyncAzureOpenAI, AsyncStream
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
from openai.lib.azure import AsyncAzureADTokenProvider
from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice
from pydantic import ValidationError

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.azure_config_base import (
    AzureOpenAIConfigBase,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion_base import (
    OpenAIChatCompletionBase,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import (
    OpenAIModelTypes,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion_base import (
    OpenAITextCompletionBase,
)
from semantic_kernel.connectors.ai.open_ai.settings.azure_open_ai_settings import (
    AzureOpenAISettings,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import (
    PromptExecutionSettings,
)
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
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
<<<<<<< main
=======
>>>>>>> Stashed changes
>>>>>>> head
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.azure_config_base import AzureOpenAIConfigBase
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion_base import OpenAIChatCompletionBase
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import OpenAIModelTypes
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion_base import OpenAITextCompletionBase
from semantic_kernel.connectors.ai.open_ai.settings.azure_open_ai_settings import AzureOpenAISettings
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
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
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.streaming_chat_message_content import (
    StreamingChatMessageContent,
)
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError
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
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
>>>>>>> head
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_role import ChatRole
from semantic_kernel.contents.finish_reason import FinishReason
from semantic_kernel.kernel_pydantic import HttpsUrl
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError, ServiceInvalidResponseError
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import trace_streaming_chat_completion
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

logger: logging.Logger = logging.getLogger(__name__)

TChatMessageContent = TypeVar(
    "TChatMessageContent", ChatMessageContent, StreamingChatMessageContent
)


class AzureChatCompletion(
    AzureOpenAIConfigBase, OpenAIChatCompletionBase, OpenAITextCompletionBase
):
    """Azure Chat completion class."""

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
        token_endpoint: str | None = None,
        default_headers: Mapping[str, str] | None = None,
        async_client: AsyncAzureOpenAI | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
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
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
    ) -> None:
        """Initialize an AzureChatCompletion service.

        Args:
            service_id (str | None): The service ID for the Azure deployment. (Optional)
            api_key  (str | None): The optional api key. If provided, will override the value in the
                env vars or .env file.
            deployment_name  (str | None): The optional deployment. If provided, will override the value
                (chat_deployment_name) in the env vars or .env file.
            endpoint (str | None): The optional deployment endpoint. If provided will override the value
                in the env vars or .env file.
            base_url (str | None): The optional deployment base_url. If provided will override the value
                in the env vars or .env file.
            api_version (str | None): The optional deployment api version. If provided will override the value
                in the env vars or .env file.
            ad_token (str | None): The Azure Active Directory token. (Optional)
            ad_token_provider (AsyncAzureADTokenProvider): The Azure Active Directory token provider. (Optional)
            token_endpoint (str | None): The token endpoint to request an Azure token. (Optional)
            default_headers (Mapping[str, str]): The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            async_client (AsyncAzureOpenAI | None): An existing client to use. (Optional)
            env_file_path (str | None): Use the environment settings file as a fallback to using env vars.
            env_file_encoding (str | None): The encoding of the environment settings file, defaults to 'utf-8'.
=======
        deployment_name: str,
        base_url: Union[HttpsUrl, str],
        service_id: Optional[str] = None,
        api_version: str = DEFAULT_AZURE_API_VERSION,
        api_key: Optional[str] = None,
        ad_token: Optional[str] = None,
        ad_token_provider: Optional[AsyncAzureADTokenProvider] = None,
        default_headers: Optional[Mapping[str, str]] = None,
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
>>>>>>> Stashed changes
    ) -> None:
        """Initialize an AzureChatCompletion service.

        Args:
            service_id (str | None): The service ID for the Azure deployment. (Optional)
            api_key  (str | None): The optional api key. If provided, will override the value in the
                env vars or .env file.
            deployment_name  (str | None): The optional deployment. If provided, will override the value
                (chat_deployment_name) in the env vars or .env file.
            endpoint (str | None): The optional deployment endpoint. If provided will override the value
                in the env vars or .env file.
            base_url (str | None): The optional deployment base_url. If provided will override the value
                in the env vars or .env file.
            api_version (str | None): The optional deployment api version. If provided will override the value
                in the env vars or .env file.
            ad_token (str | None): The Azure Active Directory token. (Optional)
            ad_token_provider (AsyncAzureADTokenProvider): The Azure Active Directory token provider. (Optional)
            token_endpoint (str | None): The token endpoint to request an Azure token. (Optional)
            default_headers (Mapping[str, str]): The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            async_client (AsyncAzureOpenAI | None): An existing client to use. (Optional)
            env_file_path (str | None): Use the environment settings file as a fallback to using env vars.
            env_file_encoding (str | None): The encoding of the environment settings file, defaults to 'utf-8'.
        """
        try:
            azure_openai_settings = AzureOpenAISettings.create(
                api_key=api_key,
                base_url=base_url,
                endpoint=endpoint,
                chat_deployment_name=deployment_name,
                api_version=api_version,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
                token_endpoint=token_endpoint,
            )
        except ValidationError as exc:
            raise ServiceInitializationError(
                f"Failed to validate settings: {exc}"
            ) from exc

        if not azure_openai_settings.chat_deployment_name:
            raise ServiceInitializationError("chat_deployment_name is required.")

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
<<<<<<< Updated upstream
        # If the async_client is None, the api_key is none, the ad_token is none, and the ad_token_provider is none,
        # then we will attempt to get the ad_token using the default endpoint specified in the Azure OpenAI settings.

        # Temp debug logging
        print(f"async_client: {async_client is not None}")
        print(f"api_key: {azure_openai_settings.api_key is not None}")
        print(f"ad_token: {ad_token is not None}")
        print(f"ad_token_provider: {ad_token_provider is not None}")
        print(f"token_endpoint: {azure_openai_settings.token_endpoint is not None}")

        if (
            async_client is None
            and azure_openai_settings.api_key is None
            and ad_token_provider is None
            and ad_token is None
            and azure_openai_settings.token_endpoint
        ):
            print("Getting ad_token")
            ad_token = azure_openai_settings.get_azure_openai_auth_token(
                token_endpoint=azure_openai_settings.token_endpoint
            )
            print(f"Called get ad_token: {ad_token is not None}")

        if not async_client and not azure_openai_settings.api_key and not ad_token and not ad_token_provider:
            raise ServiceInitializationError(
                "Please provide either a custom client, or an api_key, an ad_token or an ad_token_provider"
            )

        super().__init__(
            deployment_name=azure_openai_settings.chat_deployment_name,
            endpoint=azure_openai_settings.endpoint,
            base_url=azure_openai_settings.base_url,
            api_version=azure_openai_settings.api_version,
            service_id=service_id,
            api_key=(
                azure_openai_settings.api_key.get_secret_value()
                if azure_openai_settings.api_key
                else None
            ),
    @overload
    def __init__(
        self,
        deployment_name: str,
        endpoint: Union[HttpsUrl, str],
<<<<<<< div
=======
<<<<<<< Updated upstream
>>>>>>> head
=======
        deployment_name: str,
        base_url: Union[HttpsUrl, str],
        service_id: Optional[str] = None,
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
>>>>>>> head
        api_version: str = DEFAULT_AZURE_API_VERSION,
        service_id: Optional[str] = None,
        api_key: Optional[str] = None,
        ad_token: Optional[str] = None,
        ad_token_provider: Optional[AsyncAzureADTokenProvider] = None,
        default_headers: Optional[Mapping[str, str]] = None,
<<<<<<< div
<<<<<<< div
=======
=======
<<<<<<< Updated upstream
<<<<<<< head
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
    ) -> None:
        """Initialize an AzureChatCompletion service.

        Args:
            service_id (str | None): The service ID for the Azure deployment. (Optional)
            api_key  (str | None): The optional api key. If provided, will override the value in the
                env vars or .env file.
            deployment_name  (str | None): The optional deployment. If provided, will override the value
                (chat_deployment_name) in the env vars or .env file.
            endpoint (str | None): The optional deployment endpoint. If provided will override the value
                in the env vars or .env file.
            base_url (str | None): The optional deployment base_url. If provided will override the value
                in the env vars or .env file.
            api_version (str | None): The optional deployment api version. If provided will override the value
                in the env vars or .env file.
            ad_token (str | None): The Azure Active Directory token. (Optional)
            ad_token_provider (AsyncAzureADTokenProvider): The Azure Active Directory token provider. (Optional)
            token_endpoint (str | None): The token endpoint to request an Azure token. (Optional)
            default_headers (Mapping[str, str]): The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            async_client (AsyncAzureOpenAI | None): An existing client to use. (Optional)
            env_file_path (str | None): Use the environment settings file as a fallback to using env vars.
            env_file_encoding (str | None): The encoding of the environment settings file, defaults to 'utf-8'.
        """
        try:
            azure_openai_settings = AzureOpenAISettings.create(
                api_key=api_key,
                base_url=base_url,
                endpoint=endpoint,
                chat_deployment_name=deployment_name,
                api_version=api_version,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
                token_endpoint=token_endpoint,
            )
        except ValidationError as exc:
            raise ServiceInitializationError(
                f"Failed to validate settings: {exc}"
            ) from exc

        if not azure_openai_settings.chat_deployment_name:
            raise ServiceInitializationError("chat_deployment_name is required.")

=======
>>>>>>> Stashed changes
        # If the async_client is None, the api_key is none, the ad_token is none, and the ad_token_provider is none,
        # then we will attempt to get the ad_token using the default endpoint specified in the Azure OpenAI settings.

        # Temp debug logging
        print(f"async_client: {async_client is not None}")
        print(f"api_key: {azure_openai_settings.api_key is not None}")
        print(f"ad_token: {ad_token is not None}")
        print(f"ad_token_provider: {ad_token_provider is not None}")
        print(f"token_endpoint: {azure_openai_settings.token_endpoint is not None}")

        if (
            async_client is None
            and azure_openai_settings.api_key is None
            and ad_token_provider is None
            and ad_token is None
            and azure_openai_settings.token_endpoint
        ):
            print("Getting ad_token")
            ad_token = azure_openai_settings.get_azure_openai_auth_token(
                token_endpoint=azure_openai_settings.token_endpoint
            )
            print(f"Called get ad_token: {ad_token is not None}")

        if not async_client and not azure_openai_settings.api_key and not ad_token and not ad_token_provider:
            raise ServiceInitializationError(
                "Please provide either a custom client, or an api_key, an ad_token or an ad_token_provider"
            )

        super().__init__(
            deployment_name=azure_openai_settings.chat_deployment_name,
            endpoint=azure_openai_settings.endpoint,
            base_url=azure_openai_settings.base_url,
            api_version=azure_openai_settings.api_version,
            service_id=service_id,
            api_key=(
                azure_openai_settings.api_key.get_secret_value()
                if azure_openai_settings.api_key
                else None
            ),
    @overload
    def __init__(
        self,
        deployment_name: str,
        endpoint: Union[HttpsUrl, str],
        api_version: str = DEFAULT_AZURE_API_VERSION,
        service_id: Optional[str] = None,
        api_key: Optional[str] = None,
        ad_token: Optional[str] = None,
        ad_token_provider: Optional[AsyncAzureADTokenProvider] = None,
        default_headers: Optional[Mapping[str, str]] = None,
<<<<<<< div
>>>>>>> main
=======
<<<<<<< Updated upstream
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
    ) -> None:
        """
        Initialize an AzureChatCompletion service.

        Arguments:
            deployment_name: The name of the Azure deployment. This value
                will correspond to the custom name you chose for your deployment
                when you deployed a model. This value can be found under
                Resource Management > Deployments in the Azure portal or, alternatively,
                under Management > Deployments in Azure OpenAI Studio.
            endpoint: The endpoint of the Azure deployment. This value
                can be found in the Keys & Endpoint section when examining
                your resource from the Azure portal, the endpoint should end in openai.azure.com.
            api_key: The API key for the Azure deployment. This value can be
                found in the Keys & Endpoint section when examining your resource in
                the Azure portal. You can use either KEY1 or KEY2.
            api_version: The API version to use. (Optional)
                The default value is "2023-05-15".
            ad_auth: Whether to use Azure Active Directory authentication. (Optional)
                The default value is False.
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
        """

    @overload
    def __init__(
        self,
        deployment_name: str,
        async_client: AsyncAzureOpenAI,
        service_id: Optional[str] = None,
    ) -> None:
        """
        Initialize an AzureChatCompletion service.

        Arguments:
            deployment_name: The name of the Azure deployment. This value
                will correspond to the custom name you chose for your deployment
                when you deployed a model. This value can be found under
                Resource Management > Deployments in the Azure portal or, alternatively,
                under Management > Deployments in Azure OpenAI Studio.
            async_client {AsyncAzureOpenAI} -- An existing client to use.
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
=======
        """

    @overload
    def __init__(
        self,
        deployment_name: str,
        endpoint: Union[HttpsUrl, str],
        api_version: str = DEFAULT_AZURE_API_VERSION,
        service_id: Optional[str] = None,
        api_key: Optional[str] = None,
        ad_token: Optional[str] = None,
        ad_token_provider: Optional[AsyncAzureADTokenProvider] = None,
        default_headers: Optional[Mapping[str, str]] = None,
        use_extensions: bool = False,
    ) -> None:
        """
        Initialize an AzureChatCompletion service.

        Arguments:
        deployment_name: The name of the Azure deployment. This value
            will correspond to the custom name you chose for your deployment
            when you deployed a model. This value can be found under
            Resource Management > Deployments in the Azure portal or, alternatively,
            under Management > Deployments in Azure OpenAI Studio.
        endpoint: The endpoint of the Azure deployment. This value
            can be found in the Keys & Endpoint section when examining
            your resource from the Azure portal, the endpoint should end in openai.azure.com.
        api_key: The API key for the Azure deployment. This value can be
            found in the Keys & Endpoint section when examining your resource in
            the Azure portal. You can use either KEY1 or KEY2.
        api_version: The API version to use. (Optional)
            The default value is "2023-05-15".
        ad_auth: Whether to use Azure Active Directory authentication. (Optional)
            The default value is False.
        default_headers: The default headers mapping of string keys to
            string values for HTTP requests. (Optional)
        log: The logger instance to use. (Optional)
        use_extensions: Whether to use extensions, for example when chatting with data. (Optional)
            When True, base_url is overwritten to '{endpoint}/openai/deployments/{deployment_name}/extensions'.
            The default value is False.
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
        """

    @overload
    def __init__(
        self,
        deployment_name: str,
        endpoint: Union[HttpsUrl, str],
        api_version: str = DEFAULT_AZURE_API_VERSION,
        service_id: Optional[str] = None,
        api_key: Optional[str] = None,
        ad_token: Optional[str] = None,
        ad_token_provider: Optional[AsyncAzureADTokenProvider] = None,
        default_headers: Optional[Mapping[str, str]] = None,
        use_extensions: bool = False,
    ) -> None:
        """
        Initialize an AzureChatCompletion service.

        Arguments:
        deployment_name: The name of the Azure deployment. This value
            will correspond to the custom name you chose for your deployment
            when you deployed a model. This value can be found under
            Resource Management > Deployments in the Azure portal or, alternatively,
            under Management > Deployments in Azure OpenAI Studio.
        endpoint: The endpoint of the Azure deployment. This value
            can be found in the Keys & Endpoint section when examining
            your resource from the Azure portal, the endpoint should end in openai.azure.com.
        api_key: The API key for the Azure deployment. This value can be
            found in the Keys & Endpoint section when examining your resource in
            the Azure portal. You can use either KEY1 or KEY2.
        api_version: The API version to use. (Optional)
            The default value is "2023-05-15".
        ad_auth: Whether to use Azure Active Directory authentication. (Optional)
            The default value is False.
        default_headers: The default headers mapping of string keys to
            string values for HTTP requests. (Optional)
        log: The logger instance to use. (Optional)
        use_extensions: Whether to use extensions, for example when chatting with data. (Optional)
            When True, base_url is overwritten to '{endpoint}/openai/deployments/{deployment_name}/extensions'.
            The default value is False.
>>>>>>> origin/main
        """
        try:
            azure_openai_settings = AzureOpenAISettings.create(
                api_key=api_key,
                base_url=base_url,
                endpoint=endpoint,
                chat_deployment_name=deployment_name,
                api_version=api_version,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
                token_endpoint=token_endpoint,
            )
        except ValidationError as exc:
            raise ServiceInitializationError(
                f"Failed to validate settings: {exc}"
            ) from exc

        if not azure_openai_settings.chat_deployment_name:
            raise ServiceInitializationError("chat_deployment_name is required.")

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
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        # If the api_key is none, and the ad_token is none, and the ad_token_provider is none,
        # then we will attempt to get the ad_token using the default endpoint specified in the Azure OpenAI settings.
        if api_key is None and ad_token_provider is None and azure_openai_settings.token_endpoint and ad_token is None:
            ad_token = azure_openai_settings.get_azure_openai_auth_token(
                token_endpoint=azure_openai_settings.token_endpoint
            )

        if not azure_openai_settings.api_key and not ad_token and not ad_token_provider:
            raise ServiceInitializationError(
                "Please provide either api_key, ad_token or ad_token_provider"
            )

<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
<<<<<<< main
>>>>>>> Stashed changes
        super().__init__(
            deployment_name=azure_openai_settings.chat_deployment_name,
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
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    def __init__(
        self,
        deployment_name: str,
        endpoint: Optional[Union[HttpsUrl, str]] = None,
        base_url: Optional[Union[HttpsUrl, str]] = None,
        api_version: str = DEFAULT_AZURE_API_VERSION,
        service_id: Optional[str] = None,
        api_key: Optional[str] = None,
        ad_token: Optional[str] = None,
        ad_token_provider: Optional[AsyncAzureADTokenProvider] = None,
        default_headers: Optional[Mapping[str, str]] = None,
        async_client: Optional[AsyncAzureOpenAI] = None,
        use_extensions: bool = False,
    ) -> None:
        """
        Initialize an AzureChatCompletion service.

        Arguments:
            deployment_name: The name of the Azure deployment. This value
                will correspond to the custom name you chose for your deployment
                when you deployed a model. This value can be found under
                Resource Management > Deployments in the Azure portal or, alternatively,
                under Management > Deployments in Azure OpenAI Studio.
            base_url: The url of the Azure deployment. This value
                can be found in the Keys & Endpoint section when examining
                your resource from the Azure portal, the base_url consists of the endpoint,
                followed by /openai/deployments/{deployment_name}/,
                use endpoint if you only want to supply the endpoint.
            endpoint: The endpoint of the Azure deployment. This value
                can be found in the Keys & Endpoint section when examining
                your resource from the Azure portal, the endpoint should end in openai.azure.com.
                If both base_url and endpoint are supplied, base_url will be used.
            api_key: The API key for the Azure deployment. This value can be
                found in the Keys & Endpoint section when examining your resource in
                the Azure portal. You can use either KEY1 or KEY2.
            api_version: The API version to use. (Optional)
                The default value is "2023-05-15".
            ad_auth: Whether to use Azure Active Directory authentication. (Optional)
                The default value is False.
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            async_client {Optional[AsyncAzureOpenAI]} -- An existing client to use. (Optional)
            use_extensions: Whether to use extensions, for example when chatting with data. (Optional)
                When True, base_url is overwritten to '{endpoint}/openai/deployments/{deployment_name}/extensions'.
                The default value is False.
        """
        if base_url and isinstance(base_url, str):
            base_url = HttpsUrl(base_url)
        if use_extensions and endpoint and deployment_name:
            base_url = HttpsUrl(f"{str(endpoint).rstrip('/')}/openai/deployments/{deployment_name}/extensions")
        super().__init__(
            deployment_name=deployment_name,
            endpoint=endpoint if not isinstance(endpoint, str) else HttpsUrl(endpoint),
            base_url=base_url,
            api_version=api_version,
            service_id=service_id,
            api_key=api_key,
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
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
            ad_token=ad_token,
            ad_token_provider=ad_token_provider,
            default_headers=default_headers,
            ai_model_type=OpenAIModelTypes.CHAT,
            client=async_client,
        )

<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
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
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
    @classmethod
    def from_dict(cls, settings: dict[str, Any]) -> "AzureChatCompletion":
        """Initialize an Azure OpenAI service from a dictionary of settings.

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
    @override
    @trace_streaming_chat_completion(OpenAIChatCompletionBase.MODEL_PROVIDER_NAME)
    async def _inner_get_streaming_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
        """Override the base method.

        This is because the latest Azure OpenAI API GA version doesn't support `stream_option`
        yet and it will potentially result in errors if the option is included.
        This method will be called instead of the base method.
        TODO: Remove this method when the `stream_option` is supported by the Azure OpenAI API.
        GitHub Issue: https://github.com/microsoft/semantic-kernel/issues/8996
        """
        if not isinstance(settings, OpenAIChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, OpenAIChatPromptExecutionSettings)  # nosec

        settings.stream = True
        settings.messages = self._prepare_chat_history_for_request(chat_history)
        settings.ai_model_id = settings.ai_model_id or self.ai_model_id

        response = await self._send_request(request_settings=settings)
        if not isinstance(response, AsyncStream):
            raise ServiceInvalidResponseError("Expected an AsyncStream[ChatCompletionChunk] response.")
        async for chunk in response:
            if len(chunk.choices) == 0:
                continue

            assert isinstance(chunk, ChatCompletionChunk)  # nosec
            chunk_metadata = self._get_metadata_from_streaming_chat_response(chunk)
            yield [
                self._create_streaming_chat_message_content(chunk, choice, chunk_metadata) for choice in chunk.choices
            ]

<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
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
    @classmethod
    def from_dict(cls, settings: dict[str, Any]) -> "AzureChatCompletion":
        """Initialize an Azure OpenAI service from a dictionary of settings.

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
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
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
        Args:
            settings: A dictionary of settings for the service.
                should contain keys: service_id, and optionally:
                    ad_auth, ad_token_provider, default_headers
        """
        return AzureChatCompletion(
            service_id=settings.get("service_id"),
            api_key=settings.get("api_key"),
            deployment_name=settings.get("deployment_name"),
            endpoint=settings.get("endpoint"),
            base_url=settings.get("base_url"),
            api_version=settings.get("api_version"),
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
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
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> Stashed changes
>>>>>>> head
            api_version=settings.get("api_version", DEFAULT_AZURE_API_VERSION),
            service_id=settings.get("service_id"),
            api_key=settings.get("api_key"),
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
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
            ad_token=settings.get("ad_token"),
            ad_token_provider=settings.get("ad_token_provider"),
            default_headers=settings.get("default_headers"),
            env_file_path=settings.get("env_file_path"),
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
        )

    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        """Create a request settings object."""
        return AzureChatPromptExecutionSettings

    def _create_chat_message_content(
        self,
        response: ChatCompletion,
        choice: Choice,
        response_metadata: dict[str, Any],
    ) -> ChatMessageContent:
        """Create an Azure chat message content object from a choice."""
        content = super()._create_chat_message_content(
            response, choice, response_metadata
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
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        )
        return self._add_tool_message_to_chat_message_content(content, choice)

    def _create_streaming_chat_message_content(
        self,
        chunk: ChatCompletionChunk,
        choice: ChunkChoice,
        chunk_metadata: dict[str, Any],
    ) -> "StreamingChatMessageContent":
        """Create an Azure streaming chat message content object from a choice."""
        content = super()._create_streaming_chat_message_content(
            chunk, choice, chunk_metadata
        )
=======
<<<<<<< Updated upstream
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
        )
        return self._add_tool_message_to_chat_message_content(content, choice)

    def _create_streaming_chat_message_content(
        self,
        chunk: ChatCompletionChunk,
        choice: ChunkChoice,
        chunk_metadata: dict[str, Any],
    ) -> "StreamingChatMessageContent":
        """Create an Azure streaming chat message content object from a choice."""
        content = super()._create_streaming_chat_message_content(
            chunk, choice, chunk_metadata
        )
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
        )

    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        """Create a request settings object."""
        return AzureChatPromptExecutionSettings

    def _create_chat_message_content(
        self,
        response: ChatCompletion,
        choice: Choice,
        response_metadata: dict[str, Any],
    ) -> ChatMessageContent:
        """Create an Azure chat message content object from a choice."""
        content = super()._create_chat_message_content(
            response, choice, response_metadata
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
        )
        return self._add_tool_message_to_chat_message_content(content, choice)

    def _create_streaming_chat_message_content(
        self,
        chunk: ChatCompletionChunk,
        choice: ChunkChoice,
        chunk_metadata: dict[str, Any],
    ) -> "StreamingChatMessageContent":
        """Create an Azure streaming chat message content object from a choice."""
        content = super()._create_streaming_chat_message_content(
            chunk, choice, chunk_metadata
        )
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
>>>>>>> head
        assert isinstance(content, StreamingChatMessageContent) and isinstance(
            choice, ChunkChoice
        )  # nosec
        return self._add_tool_message_to_chat_message_content(content, choice)

    def _add_tool_message_to_chat_message_content(
        self,
        content: TChatMessageContent,
        choice: Choice | ChunkChoice,
    ) -> TChatMessageContent:
        if tool_message := self._get_tool_message_from_chat_choice(choice=choice):
            if not isinstance(tool_message, dict):
                # try to json, to ensure it is a dictionary
                try:
                    tool_message = json.loads(tool_message)
                except json.JSONDecodeError:
                    logger.warning("Tool message is not a dictionary, ignore context.")
                    return content
            function_call = FunctionCallContent(
                id=str(uuid4()),
                name="Azure-OnYourData",
                arguments=json.dumps({"query": tool_message.get("intent", [])}),
            )
            result = FunctionResultContent.from_function_call_content_and_result(
                result=tool_message["citations"], function_call_content=function_call
            )
            content.items.insert(0, function_call)
            content.items.insert(1, result)
        return content

    def _get_tool_message_from_chat_choice(
        self, choice: Choice | ChunkChoice
    ) -> dict[str, Any] | None:
        """Get the tool message from a choice."""
        content = choice.message if isinstance(choice, Choice) else choice.delta
        # When you enable asynchronous content filtering in Azure OpenAI, you may receive empty deltas
        if content and content.model_extra is not None:
            return content.model_extra.get("context", None)
        # openai allows extra content, so model_extra will be a dict, but we need to check anyway, but no way to test.
        return None  # pragma: no cover

    @staticmethod
    def split_message(message: "ChatMessageContent") -> list["ChatMessageContent"]:
        """Split an Azure On Your Data response into separate ChatMessageContents.

        If the message does not have three contents, and those three are one each of:
        FunctionCallContent, FunctionResultContent, and TextContent,
        it will not return three messages, potentially only one or two.

        The order of the returned messages is as expected by OpenAI.
        """
        if len(message.items) != 3:
            return [message]
        messages = {
            "tool_call": deepcopy(message),
            "tool_result": deepcopy(message),
            "assistant": deepcopy(message),
        }
        for key, msg in messages.items():
            if key == "tool_call":
                msg.items = [
                    item for item in msg.items if isinstance(item, FunctionCallContent)
                ]
                msg.finish_reason = FinishReason.FUNCTION_CALL
            if key == "tool_result":
                msg.items = [
                    item
                    for item in msg.items
                    if isinstance(item, FunctionResultContent)
                ]
            if key == "assistant":
                msg.items = [
                    item for item in msg.items if isinstance(item, TextContent)
                ]
        return [messages["tool_call"], messages["tool_result"], messages["assistant"]]
