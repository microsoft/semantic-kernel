# Copyright (c) Microsoft. All rights reserved.


from dataclasses import asdict
from logging import Logger
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

from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings
from semantic_kernel.connectors.ai.open_ai.const import DEFAULT_AZURE_API_VERSION
from semantic_kernel.connectors.ai.open_ai.models.chat.azure_chat_with_data_response import (
    AzureChatWithDataStreamResponse,
)
from semantic_kernel.connectors.ai.open_ai.models.chat.function_call import FunctionCall
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
from semantic_kernel.connectors.ai.open_ai.utils import _parse_message
from semantic_kernel.sk_pydantic import HttpsUrl


class AzureChatCompletion(
    AzureOpenAIConfigBase, OpenAIChatCompletionBase, OpenAITextCompletionBase
):
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
        log: Optional[Logger] = None,
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
            log: The logger instance to use. (Optional)
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
        log: Optional[Logger] = None,
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
            logger: deprecated, use 'log' instead.
        """

    @overload
    def __init__(
        self,
        deployment_name: str,
        async_client: AsyncAzureOpenAI,
        log: Optional[Logger] = None,
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
            log: The logger instance to use. (Optional)
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
        log: Optional[Logger] = None,
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
        log: Optional[Logger] = None,
        logger: Optional[Logger] = None,
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
            log: The logger instance to use. (Optional)
            logger: deprecated, use 'log' instead.
            async_client {Optional[AsyncAzureOpenAI]} -- An existing client to use. (Optional)
            use_extensions: Whether to use extensions, for example when chatting with data. (Optional)
                When True, base_url is overwritten to '{endpoint}/openai/deployments/{deployment_name}/extensions'.
                The default value is False.
        """
        if logger:
            logger.warning("The 'logger' argument is deprecated, use 'log' instead.")

        if use_extensions:
            base_url = f"{str(endpoint).rstrip('/')}/openai/deployments/{deployment_name}/extensions"

        if isinstance(endpoint, str):
            endpoint = HttpsUrl(endpoint)
        if isinstance(base_url, str):
            base_url = HttpsUrl(base_url)
        super().__init__(
            deployment_name=deployment_name,
            endpoint=endpoint,
            base_url=base_url,
            api_version=api_version,
            api_key=api_key,
            ad_token=ad_token,
            ad_token_provider=ad_token_provider,
            default_headers=default_headers,
            log=log or logger,
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
                and optionally: api_version, ad_auth, default_headers, log
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
            log=settings.get("log"),
        )

    async def complete_chat_with_data_async(
        self,
        messages: List[Dict[str, str]],
        request_settings: "ChatRequestSettings",
        logger: Optional[Logger] = None,
        functions: Optional[List[Dict[str, Any]]] = None,
    ) -> Union[
        Tuple[str, str],
        List[Tuple[str, str]],
        Tuple[Optional[str], Optional[str], Optional[FunctionCall]],
        List[Tuple[Optional[str], Optional[str], Optional[FunctionCall]]],
    ]:
        """Executes a chat completion request with data (and optionally functions) and returns the result.

        Arguments:
            messages {List[Tuple[str,str]]} -- The messages to use for the chat completion.
            request_settings {ChatRequestSettings} -- The settings to use for the chat completion request.
            logger {Optional[Logger]} -- The logger instance to use. (Optional)
            functions {Optional[List[Dict[str, Any]]]} -- The functions to use for the chat completion. (Optional)

        Returns:
            The completion result(s) in the format (assistant_message, tool_message) or
            (assistant_message, tool_message, function_call).
            The tool message contains additional information about the data source including citations.
        """
        response = await self._send_request(
            messages=messages,
            request_settings=request_settings,
            stream=False,
            functions=functions,
        )

        if len(response.choices) == 1:
            return _parse_message(response.choices[0].message, with_data=True)
        else:
            return [_parse_message(choice.message) for choice in response.choices]

    async def complete_chat_stream_with_data_async(
        self,
        messages: List[Dict[str, str]],
        settings: "ChatRequestSettings",
        logger: Optional[Logger] = None,
    ) -> AsyncGenerator[Union[str, List[str]], None]:
        """Executes a chat completion request with data and returns the result.

        Arguments:
            messages {List[Tuple[str,str]]} -- The messages to use for the chat completion.
            settings {ChatRequestSettings} -- The settings to use for the chat completion request.
            logger {Optional[Logger]} -- The logger instance to use. (Optional)

        Returns:
            Union[str, List[str]] -- The completion result(s).
        """
        response = await self._send_request(
            messages=messages, request_settings=settings, stream=True
        )

        return AzureChatWithDataStreamResponse(response, settings)

    def _create_model_args(
        self, request_settings, stream, prompt, messages, functions, chat_mode
    ):
        model_args = super()._create_model_args(
            request_settings, stream, prompt, messages, functions, chat_mode
        )

        if (
            hasattr(request_settings, "data_source_settings")
            and request_settings.data_source_settings is not None
        ):
            model_args["extra_body"] = asdict(request_settings.data_source_settings)

            # Remove embeddingDeploymentName if not using vector search.
            if (
                model_args["extra_body"]["dataSources"][0]["parameters"][
                    "embeddingDeploymentName"
                ]
                is None
            ):
                del model_args["extra_body"]["dataSources"][0]["parameters"][
                    "embeddingDeploymentName"
                ]

            if request_settings.inputLanguage is not None:
                model_args["extra_body"][
                    "inputLanguage"
                ] = request_settings.inputLanguage
            if request_settings.outputLanguage is not None:
                model_args["extra_body"][
                    "outputLanguage"
                ] = request_settings.outputLanguage

            # Remove args that are not supported by the with-data extensions API (yet).
            del model_args["n"]
            del model_args["logit_bias"]
            del model_args["presence_penalty"]
            del model_args["frequency_penalty"]

        return model_args
