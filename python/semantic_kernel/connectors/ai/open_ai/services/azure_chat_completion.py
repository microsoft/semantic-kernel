# Copyright (c) Microsoft. All rights reserved.


import logging
from typing import (
    Any,
    AsyncGenerator,
    Dict,
    List,
    Mapping,
    Optional,
    Tuple,
    Union,
    overload,
)

from openai import AsyncAzureOpenAI
from openai.lib.azure import AsyncAzureADTokenProvider

from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.open_ai.const import DEFAULT_AZURE_API_VERSION
from semantic_kernel.connectors.ai.open_ai.models.chat.azure_chat_with_data_response import (
    AzureChatWithDataStreamResponse,
)
from semantic_kernel.connectors.ai.open_ai.models.chat.function_call import FunctionCall
from semantic_kernel.connectors.ai.open_ai.request_settings.azure_chat_request_settings import (
    AzureChatRequestSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.azure_config_base import (
    AzureOpenAIConfigBase,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import (
    OpenAIModelTypes,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion_base import (
    OpenAITextCompletionBase,
)
from semantic_kernel.connectors.ai.open_ai.utils import _parse_choices, _parse_message
from semantic_kernel.kernel_pydantic import HttpsUrl

logger: logging.Logger = logging.getLogger(__name__)


class AzureChatCompletion(AzureOpenAIConfigBase, ChatCompletionClientBase, OpenAITextCompletionBase):
    """Azure Chat completion class."""

    @overload
    def __init__(
        self,
        deployment_name: str,
        base_url: Union[HttpsUrl, str],
        api_version: str = DEFAULT_AZURE_API_VERSION,
        api_key: Optional[str] = None,
        ad_token: Optional[str] = None,
        ad_token_provider: Optional[AsyncAzureADTokenProvider] = None,
        default_headers: Optional[Mapping[str, str]] = None,
        log: Optional[Any] = None,
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
            api_key: The API key for the Azure deployment. This value can be
                found in the Keys & Endpoint section when examining your resource in
                the Azure portal. You can use either KEY1 or KEY2.
            api_version: The API version to use. (Optional)
                The default value is "2023-05-15".
            ad_auth: Whether to use Azure Active Directory authentication. (Optional)
                The default value is False.
            default_headers: The default headers mapping of string keys to
                string values for HTTP requests. (Optional)
            log: The logger instance to use. (Optional) (Deprecated)
            logger: deprecated, use 'log' instead.
        """

    @overload
    def __init__(
        self,
        deployment_name: str,
        endpoint: Union[HttpsUrl, str],
        api_version: str = DEFAULT_AZURE_API_VERSION,
        api_key: Optional[str] = None,
        ad_token: Optional[str] = None,
        ad_token_provider: Optional[AsyncAzureADTokenProvider] = None,
        default_headers: Optional[Mapping[str, str]] = None,
        log: Optional[Any] = None,
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
            log: The logger instance to use. (Optional) (Deprecated)
            logger: deprecated, use 'log' instead.
        """

    @overload
    def __init__(
        self,
        deployment_name: str,
        async_client: AsyncAzureOpenAI,
        log: Optional[Any] = None,
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
            log: The logger instance to use. (Optional) (Deprecated)
        """

    @overload
    def __init__(
        self,
        deployment_name: str,
        endpoint: Union[HttpsUrl, str],
        api_version: str = DEFAULT_AZURE_API_VERSION,
        api_key: Optional[str] = None,
        ad_token: Optional[str] = None,
        ad_token_provider: Optional[AsyncAzureADTokenProvider] = None,
        default_headers: Optional[Mapping[str, str]] = None,
        log: Optional[Any] = None,
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
        """

    def __init__(
        self,
        deployment_name: str,
        endpoint: Optional[Union[HttpsUrl, str]] = None,
        base_url: Optional[Union[HttpsUrl, str]] = None,
        api_version: str = DEFAULT_AZURE_API_VERSION,
        api_key: Optional[str] = None,
        ad_token: Optional[str] = None,
        ad_token_provider: Optional[AsyncAzureADTokenProvider] = None,
        default_headers: Optional[Mapping[str, str]] = None,
        async_client: Optional[AsyncAzureOpenAI] = None,
        use_extensions: bool = False,
        log: Optional[Any] = None,
        **kwargs,
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
            log: The logger instance to use. (Optional) (Deprecated)
            logger: deprecated.
            async_client {Optional[AsyncAzureOpenAI]} -- An existing client to use. (Optional)
            use_extensions: Whether to use extensions, for example when chatting with data. (Optional)
                When True, base_url is overwritten to '{endpoint}/openai/deployments/{deployment_name}/extensions'.
                The default value is False.
        """
        if log:
            logger.warning("The `log` parameter is deprecated. Please use the `logging` module instead.")
        if kwargs.get("logger"):
            logger.warning("The 'logger' argument is deprecated. Please use the `logging` module instead.")

        if base_url and isinstance(base_url, str):
            base_url = HttpsUrl(base_url)
        if use_extensions and endpoint and deployment_name:
            base_url = HttpsUrl(f"{str(endpoint).rstrip('/')}/openai/deployments/{deployment_name}/extensions")
        super().__init__(
            deployment_name=deployment_name,
            endpoint=endpoint if not isinstance(endpoint, str) else HttpsUrl(endpoint),
            base_url=base_url,
            api_version=api_version,
            api_key=api_key,
            ad_token=ad_token,
            ad_token_provider=ad_token_provider,
            default_headers=default_headers,
            ai_model_type=OpenAIModelTypes.CHAT,
            async_client=async_client,
        )

    @classmethod
    def from_dict(cls, settings: Dict[str, str]) -> "AzureChatCompletion":
        """
        Initialize an Azure OpenAI service from a dictionary of settings.

        Arguments:
            settings: A dictionary of settings for the service.
                should contains keys: deployment_name, endpoint, api_key
                and optionally: api_version, ad_auth, default_headers
        """
        return AzureChatCompletion(
            deployment_name=settings.get("deployment_name"),
            endpoint=settings.get("endpoint"),
            base_url=settings.get("base_url"),
            api_version=settings.get("api_version", DEFAULT_AZURE_API_VERSION),
            api_key=settings.get("api_key"),
            ad_token=settings.get("ad_token"),
            ad_token_provider=settings.get("ad_token_provider"),
            default_headers=settings.get("default_headers"),
        )

    async def complete_chat_async(
        self,
        messages: List[Dict[str, str]],
        settings: AzureChatRequestSettings,
        logger: Optional[Any] = None,
    ) -> Union[Tuple[Optional[str], Optional[FunctionCall]], List[Tuple[Optional[str], Optional[FunctionCall]]],]:
        """Executes a chat completion request and returns the result.

        Arguments:
            messages {List[Tuple[str,str]]} -- The messages to use for the chat completion.
            settings {OpenAIRequestSettings} -- The settings to use for the chat completion request.
            logger {Optional[Logger]} -- The logger instance to use. (Optional)

        Returns:
            Union[str, List[str]] -- The completion result(s).
        """
        settings.messages = messages
        settings.stream = False
        if settings.ai_model_id is None:
            settings.ai_model_id = self.ai_model_id
        response = await self._send_request(request_settings=settings)

        if len(response.choices) == 1:
            return _parse_message(
                response.choices[0].message,
                with_data=settings.extra_body is not None,
            )
        else:
            return [
                _parse_message(
                    choice.message,
                    with_data=settings.extra_body is not None,
                )
                for choice in response.choices
            ]

    async def complete_chat_stream_async(
        self,
        messages: List[Dict[str, str]],
        settings: AzureChatRequestSettings,
        logger: Optional[Any] = None,
    ) -> Union[AsyncGenerator[Union[str, List[str]], None], AzureChatWithDataStreamResponse]:
        """Executes a chat completion request and returns the result.

        Arguments:
            messages {List[Tuple[str,str]]} -- The messages to use for the chat completion.
            settings {OpenAIRequestSettings} -- The settings to use for the chat completion request.
            logger {Optional[Logger]} -- The logger instance to use. (Optional)

        Returns:
            Union[str, List[str]] -- The completion result(s).
        """
        settings.messages = messages
        settings.stream = True
        if settings.ai_model_id is None:
            settings.ai_model_id = self.ai_model_id
        response = await self._send_request(request_settings=settings)
        if settings.extra_body is not None:
            yield AzureChatWithDataStreamResponse(response, settings)
        else:
            # parse the completion text(s) and yield them
            async for chunk in response:
                if len(chunk.choices) == 0:
                    continue
                # if multiple responses are requested, keep track of them
                if settings.number_of_responses > 1:
                    completions = [""] * settings.number_of_responses
                    for choice in chunk.choices:
                        text, index = _parse_choices(choice)
                        completions[index] = text
                    yield completions
                # if only one response is requested, yield it
                else:
                    text, index = _parse_choices(chunk.choices[0])
                    yield text

    def get_request_settings_class(self) -> "AIRequestSettings":
        """Create a request settings object."""
        return AzureChatRequestSettings
