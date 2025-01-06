# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import AsyncGenerator, Callable
from typing import TYPE_CHECKING, Any, ClassVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from azure.ai.inference.aio import ChatCompletionsClient
from azure.ai.inference.models import (
    AsyncStreamingChatCompletions,
    ChatChoice,
    ChatCompletions,
    ChatCompletionsToolCall,
    ChatRequestMessage,
    StreamingChatChoiceUpdate,
    StreamingChatCompletionsUpdate,
)

from semantic_kernel.connectors.ai.azure_ai_inference import AzureAIInferenceChatPromptExecutionSettings
from semantic_kernel.connectors.ai.azure_ai_inference.services.azure_ai_inference_base import (
    AzureAIInferenceBase,
    AzureAIInferenceClientType,
)
from semantic_kernel.connectors.ai.azure_ai_inference.services.azure_ai_inference_tracing import AzureAIInferenceTracing
from semantic_kernel.connectors.ai.azure_ai_inference.services.utils import MESSAGE_CONVERTERS
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.completion_usage import CompletionUsage
from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
from semantic_kernel.connectors.ai.function_calling_utils import update_settings_from_function_call_configuration
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceType
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ITEM_TYPES, ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.streaming_chat_message_content import ITEM_TYPES as STREAMING_ITEM_TYPES
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.exceptions.service_exceptions import ServiceInvalidExecutionSettingsError
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class AzureAIInferenceChatCompletion(ChatCompletionClientBase, AzureAIInferenceBase):
    """Azure AI Inference Chat Completion Service."""

    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = True

    def __init__(
        self,
        ai_model_id: str,
        api_key: str | None = None,
        endpoint: str | None = None,
        service_id: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        client: ChatCompletionsClient | None = None,
    ) -> None:
        """Initialize the Azure AI Inference Chat Completion service.

        If no arguments are provided, the service will attempt to load the settings from the environment.
        The following environment variables are used:
        - AZURE_AI_INFERENCE_API_KEY
        - AZURE_AI_INFERENCE_ENDPOINT

        Args:
            ai_model_id: (str): A string that is used to identify the model such as the model name. (Required)
            api_key (str | None): The API key for the Azure AI Inference service deployment. (Optional)
            endpoint (str | None): The endpoint of the Azure AI Inference service deployment. (Optional)
            service_id (str | None): Service ID for the chat completion service. (Optional)
            env_file_path (str | None): The path to the environment file. (Optional)
            env_file_encoding (str | None): The encoding of the environment file. (Optional)
            client (ChatCompletionsClient | None): The Azure AI Inference client to use. (Optional)

        Raises:
            ServiceInitializationError: If an error occurs during initialization.
        """
        super().__init__(
            ai_model_id=ai_model_id,
            service_id=service_id or ai_model_id,
            client_type=AzureAIInferenceClientType.ChatCompletions,
            api_key=api_key,
            endpoint=endpoint,
            env_file_path=env_file_path,
            env_file_encoding=env_file_encoding,
            client=client,
        )

    # region Overriding base class methods

    # Override from AIServiceClientBase
    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        return AzureAIInferenceChatPromptExecutionSettings

    # Override from AIServiceClientBase
    @override
    def service_url(self) -> str | None:
        if hasattr(self.client, "_client") and hasattr(self.client._client, "_base_url"):
            # Best effort to get the endpoint
            return self.client._client._base_url
        return None

    @override
    async def _inner_get_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> list["ChatMessageContent"]:
        if not isinstance(settings, AzureAIInferenceChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, AzureAIInferenceChatPromptExecutionSettings)  # nosec

        assert isinstance(self.client, ChatCompletionsClient)  # nosec
        with AzureAIInferenceTracing():
            response: ChatCompletions = await self.client.complete(
                messages=self._prepare_chat_history_for_request(chat_history),
                model_extras=settings.extra_parameters,
                **settings.prepare_settings_dict(),
            )
        response_metadata = self._get_metadata_from_response(response)

        return [self._create_chat_message_content(response, choice, response_metadata) for choice in response.choices]

    @override
    async def _inner_get_streaming_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
        function_invoke_attempt: int = 0,
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
        if not isinstance(settings, AzureAIInferenceChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, AzureAIInferenceChatPromptExecutionSettings)  # nosec

        assert isinstance(self.client, ChatCompletionsClient)  # nosec
        with AzureAIInferenceTracing():
            response: AsyncStreamingChatCompletions = await self.client.complete(
                stream=True,
                messages=self._prepare_chat_history_for_request(chat_history),
                model_extras=settings.extra_parameters,
                **settings.prepare_settings_dict(),
            )

        async for chunk in response:
            if len(chunk.choices) == 0:
                continue
            chunk_metadata = self._get_metadata_from_response(chunk)
            yield [
                self._create_streaming_chat_message_content(chunk, choice, chunk_metadata, function_invoke_attempt)
                for choice in chunk.choices
            ]

    @override
    def _verify_function_choice_settings(self, settings: "PromptExecutionSettings") -> None:
        if not isinstance(settings, AzureAIInferenceChatPromptExecutionSettings):
            raise ServiceInvalidExecutionSettingsError(
                "The settings must be an AzureAIInferenceChatPromptExecutionSettings."
            )
        if settings.extra_parameters is not None and settings.extra_parameters.get("n", 1) > 1:
            # Currently only OpenAI models allow multiple completions but the Azure AI Inference service
            # does not expose the functionality directly. If users want to have more than 1 responses, they
            # need to configure `extra_parameters` with a key of "n" and a value greater than 1.
            raise ServiceInvalidExecutionSettingsError(
                "Auto invocation of tool calls may only be used with a single completion."
            )

    @override
    def _update_function_choice_settings_callback(
        self,
    ) -> Callable[[FunctionCallChoiceConfiguration, "PromptExecutionSettings", FunctionChoiceType], None]:
        return update_settings_from_function_call_configuration

    @override
    def _reset_function_choice_settings(self, settings: "PromptExecutionSettings") -> None:
        if hasattr(settings, "tool_choice"):
            settings.tool_choice = None
        if hasattr(settings, "tools"):
            settings.tools = None

    @override
    def _prepare_chat_history_for_request(
        self,
        chat_history: ChatHistory,
        role_key: str = "role",
        content_key: str = "content",
    ) -> list[ChatRequestMessage]:
        chat_request_messages: list[ChatRequestMessage] = []

        for message in chat_history.messages:
            chat_request_messages.append(MESSAGE_CONVERTERS[message.role](message))

        return chat_request_messages

    # endregion

    # region Non-streaming

    def _create_chat_message_content(
        self, response: ChatCompletions, choice: ChatChoice, metadata: dict[str, Any]
    ) -> ChatMessageContent:
        """Create a chat message content object.

        Args:
            response: The response from the service.
            choice: The choice from the response.
            metadata: The metadata from the response.

        Returns:
            A chat message content object.
        """
        items: list[ITEM_TYPES] = []
        if choice.message.content:
            items.append(
                TextContent(
                    text=choice.message.content,
                    inner_content=response,
                    metadata=metadata,
                )
            )
        if choice.message.tool_calls:
            for tool_call in choice.message.tool_calls:
                if isinstance(tool_call, ChatCompletionsToolCall):
                    items.append(
                        FunctionCallContent(
                            id=tool_call.id,
                            name=tool_call.function.name,
                            arguments=tool_call.function.arguments,
                        )
                    )

        return ChatMessageContent(
            role=AuthorRole(choice.message.role),
            items=items,
            inner_content=response,
            finish_reason=FinishReason(choice.finish_reason) if choice.finish_reason else None,
            metadata=metadata,
        )

    # endregion

    # region Streaming

    def _create_streaming_chat_message_content(
        self,
        chunk: AsyncStreamingChatCompletions,
        choice: StreamingChatChoiceUpdate,
        metadata: dict[str, Any],
        function_invoke_attempt: int,
    ) -> StreamingChatMessageContent:
        """Create a streaming chat message content object.

        Args:
            chunk: The chunk from the response.
            choice: The choice from the response.
            metadata: The metadata from the response.
            function_invoke_attempt: The function invoke attempt.

        Returns:
            A streaming chat message content object.
        """
        items: list[STREAMING_ITEM_TYPES] = []
        if choice.delta.content:
            items.append(
                StreamingTextContent(
                    choice_index=choice.index,
                    text=choice.delta.content,
                    inner_content=chunk,
                    metadata=metadata,
                )
            )
        if choice.delta.tool_calls:
            for tool_call in choice.delta.tool_calls:
                if isinstance(tool_call, ChatCompletionsToolCall):
                    items.append(
                        FunctionCallContent(
                            id=tool_call.id,
                            index=choice.index,
                            name=tool_call.function.name,
                            arguments=tool_call.function.arguments,
                        )
                    )

        return StreamingChatMessageContent(
            role=AuthorRole(choice.delta.role) if choice.delta.role else AuthorRole.ASSISTANT,
            items=items,
            choice_index=choice.index,
            inner_content=chunk,
            finish_reason=FinishReason(choice.finish_reason) if choice.finish_reason else None,
            metadata=metadata,
            function_invoke_attempt=function_invoke_attempt,
        )

    # endregion

    def _get_metadata_from_response(self, response: ChatCompletions | StreamingChatCompletionsUpdate) -> dict[str, Any]:
        """Get metadata from the response.

        Args:
            response: The response from the service.

        Returns:
            A dictionary containing metadata.
        """
        return {
            "id": response.id,
            "model": response.model,
            "created": response.created,
            "usage": CompletionUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
            )
            if response.usage
            else None,
        }
