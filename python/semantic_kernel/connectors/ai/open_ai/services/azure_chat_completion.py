# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from collections.abc import Mapping
from copy import deepcopy
from typing import Any, TypeVar
from uuid import uuid4

from openai import AsyncAzureOpenAI
from openai.lib.azure import AsyncAzureADTokenProvider
from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice
from pydantic import ValidationError

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.azure_config_base import AzureOpenAIConfigBase
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion_base import OpenAIChatCompletionBase
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import OpenAIModelTypes
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion_base import OpenAITextCompletionBase
from semantic_kernel.connectors.ai.open_ai.settings.azure_open_ai_settings import AzureOpenAISettings
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError

logger: logging.Logger = logging.getLogger(__name__)

TChatMessageContent = TypeVar("TChatMessageContent", ChatMessageContent, StreamingChatMessageContent)


class AzureChatCompletion(AzureOpenAIConfigBase, OpenAIChatCompletionBase, OpenAITextCompletionBase):
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
        instruction_role: str | None = None,
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
            instruction_role (str | None): The role to use for 'instruction' messages, for example, summarization
                prompts could use `developer` or `system`. (Optional)
        """
        try:
            azure_openai_settings = AzureOpenAISettings(
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
            raise ServiceInitializationError(f"Failed to validate settings: {exc}") from exc

        if not azure_openai_settings.chat_deployment_name:
            raise ServiceInitializationError("chat_deployment_name is required.")

        super().__init__(
            deployment_name=azure_openai_settings.chat_deployment_name,
            endpoint=azure_openai_settings.endpoint,
            base_url=azure_openai_settings.base_url,
            api_version=azure_openai_settings.api_version,
            service_id=service_id,
            api_key=azure_openai_settings.api_key.get_secret_value() if azure_openai_settings.api_key else None,
            ad_token=ad_token,
            ad_token_provider=ad_token_provider,
            token_endpoint=azure_openai_settings.token_endpoint,
            default_headers=default_headers,
            ai_model_type=OpenAIModelTypes.CHAT,
            client=async_client,
            instruction_role=instruction_role,
        )

    @classmethod
    def from_dict(cls, settings: dict[str, Any]) -> "AzureChatCompletion":
        """Initialize an Azure OpenAI service from a dictionary of settings.

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
            ad_token=settings.get("ad_token"),
            ad_token_provider=settings.get("ad_token_provider"),
            default_headers=settings.get("default_headers"),
            env_file_path=settings.get("env_file_path"),
        )

    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        """Create a request settings object."""
        return AzureChatPromptExecutionSettings

    def _create_chat_message_content(
        self, response: ChatCompletion, choice: Choice, response_metadata: dict[str, Any]
    ) -> ChatMessageContent:
        """Create an Azure chat message content object from a choice."""
        content = super()._create_chat_message_content(response, choice, response_metadata)
        return self._add_tool_message_to_chat_message_content(content, choice)

    def _create_streaming_chat_message_content(
        self,
        chunk: ChatCompletionChunk,
        choice: ChunkChoice,
        chunk_metadata: dict[str, Any],
        function_invoke_attempt: int = 0,
    ) -> "StreamingChatMessageContent":
        """Create an Azure streaming chat message content object from a choice."""
        content = super()._create_streaming_chat_message_content(chunk, choice, chunk_metadata, function_invoke_attempt)
        assert isinstance(content, StreamingChatMessageContent) and isinstance(choice, ChunkChoice)  # nosec
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

    def _get_tool_message_from_chat_choice(self, choice: Choice | ChunkChoice) -> dict[str, Any] | None:
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
