# Copyright (c) Microsoft. All rights reserved.
import json
import logging
from copy import deepcopy
from typing import Any, Dict, Mapping, Optional, Union, overload
from uuid import uuid4

from openai import AsyncAzureOpenAI
from openai.lib.azure import AsyncAzureADTokenProvider
from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice

from semantic_kernel.connectors.ai.open_ai.const import DEFAULT_AZURE_API_VERSION
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.azure_config_base import AzureOpenAIConfigBase
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion_base import OpenAIChatCompletionBase
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import OpenAIModelTypes
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion_base import OpenAITextCompletionBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.finish_reason import FinishReason
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.kernel_pydantic import HttpsUrl

logger: logging.Logger = logging.getLogger(__name__)


class AzureChatCompletion(AzureOpenAIConfigBase, OpenAIChatCompletionBase, OpenAITextCompletionBase):
    """Azure Chat completion class."""

    @overload
    def __init__(
        self,
        deployment_name: str,
        base_url: Union[HttpsUrl, str],
        service_id: Optional[str] = None,
        api_version: str = DEFAULT_AZURE_API_VERSION,
        api_key: Optional[str] = None,
        ad_token: Optional[str] = None,
        ad_token_provider: Optional[AsyncAzureADTokenProvider] = None,
        default_headers: Optional[Mapping[str, str]] = None,
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
        """

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
        """
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
            service_id=settings.get("service_id"),
            api_key=settings.get("api_key"),
            ad_token=settings.get("ad_token"),
            ad_token_provider=settings.get("ad_token_provider"),
            default_headers=settings.get("default_headers"),
        )

    def get_prompt_execution_settings_class(self) -> "PromptExecutionSettings":
        """Create a request settings object."""
        return AzureChatPromptExecutionSettings

    def _create_chat_message_content(
        self, response: ChatCompletion, choice: Choice, response_metadata: Dict[str, Any]
    ) -> ChatMessageContent:
        """Create a Azure chat message content object from a choice."""
        content = super()._create_chat_message_content(response, choice, response_metadata)
        return self._add_tool_message_to_chat_message_content(content, choice)

    def _create_streaming_chat_message_content(
        self,
        chunk: ChatCompletionChunk,
        choice: ChunkChoice,
        chunk_metadata: Dict[str, Any],
    ) -> "StreamingChatMessageContent":
        """Create a Azure streaming chat message content object from a choice."""
        content = super()._create_streaming_chat_message_content(chunk, choice, chunk_metadata)
        return self._add_tool_message_to_chat_message_content(content, choice)

    def _add_tool_message_to_chat_message_content(
        self, content: ChatMessageContent | StreamingChatMessageContent, choice: Choice
    ) -> "ChatMessageContent | StreamingChatMessageContent":
        if tool_message := self._get_tool_message_from_chat_choice(choice=choice):
            try:
                tool_message_dict = json.loads(tool_message)
            except json.JSONDecodeError:
                logger.error("Failed to parse tool message JSON: %s", tool_message)
                tool_message_dict = {"citations": tool_message}

            function_call = FunctionCallContent(
                id=str(uuid4()),
                name="Azure-OnYourData",
                arguments=json.dumps({"query": tool_message_dict.get("intent", [])}),
            )
            result = FunctionResultContent.from_function_call_content_and_result(
                result=tool_message_dict["citations"], function_call_content=function_call
            )
            content.items.insert(0, function_call)
            content.items.insert(1, result)
        return content

    def _get_tool_message_from_chat_choice(self, choice: Union[Choice, ChunkChoice]) -> Optional[str]:
        """Get the tool message from a choice."""
        if isinstance(choice, Choice):
            content = choice.message
        else:
            content = choice.delta
        if content.model_extra is not None and "context" in content.model_extra:
            return json.dumps(content.model_extra["context"])

        return None

    @staticmethod
    def split_message(message: "ChatMessageContent") -> list["ChatMessageContent"]:
        """Split a Azure On Your Data response into separate ChatMessageContents.

        If the message does not have three contents, and those three are one each of:
        FunctionCallContent, FunctionResultContent, and TextContent,
        it will not return three messages, potentially only one or two.

        The order of the returned messages is as expected by OpenAI.
        """
        if len(message.items) != 3:
            return [message]
        messages = {"tool_call": deepcopy(message), "tool_result": deepcopy(message), "assistant": deepcopy(message)}
        for key, msg in messages.items():
            if key == "tool_call":
                msg.items = [item for item in msg.items if isinstance(item, FunctionCallContent)]
                msg.finish_reason = FinishReason.FUNCTION_CALL
            if key == "tool_result":
                msg.items = [item for item in msg.items if isinstance(item, FunctionResultContent)]
            if key == "assistant":
                msg.items = [item for item in msg.items if isinstance(item, TextContent)]
        return [messages["tool_call"], messages["tool_result"], messages["assistant"]]
