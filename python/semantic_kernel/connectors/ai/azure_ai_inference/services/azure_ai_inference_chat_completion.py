# Copyright (c) Microsoft. All rights reserved.

from collections.abc import AsyncGenerator
from typing import Any

from azure.ai.inference import load_client as load_client_sync
from azure.ai.inference.aio import ChatCompletionsClient as ChatCompletionsClientAsync
from azure.ai.inference.models import (
    AssistantMessage,
    AsyncStreamingChatCompletions,
    ChatChoice,
    ChatCompletions,
    ChatRequestMessage,
    ModelInfo,
    ModelType,
    StreamingChatChoiceUpdate,
    SystemMessage,
    ToolMessage,
    UserMessage,
)
from azure.core.credentials import AzureKeyCredential
from pydantic import ValidationError

from semantic_kernel.connectors.ai.azure_ai_inference import (
    AzureAIInferenceChatPromptExecutionSettings,
    AzureAIInferenceSettings,
)
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError

MessageConverter: dict[AuthorRole, Any] = {
    AuthorRole.SYSTEM: SystemMessage,
    AuthorRole.USER: UserMessage,
    AuthorRole.ASSISTANT: AssistantMessage,
    AuthorRole.TOOL: ToolMessage,
}


class AzureAIInferenceChatCompletion(ChatCompletionClientBase):
    """Azure AI Inference Chat Completion Service."""

    client: ChatCompletionsClientAsync

    def __init__(
        self,
        api_key: str | None = None,
        endpoint: str | None = None,
        service_id: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize the Azure AI Inference Chat Completion service.

        Args:
            api_key: The API key for the Azure AI Inference service deployment.
            endpoint: The endpoint of the Azure AI Inference service deployment.
            service_id: Service ID for the chat completion service. (Optional)
            env_file_path: The path to the environment file. (Optional)
            env_file_encoding: The encoding of the environment file. (Optional)
        """
        try:
            azure_ai_inference_settings = AzureAIInferenceSettings.create(
                api_key=api_key,
                endpoint=endpoint,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as e:
            raise ServiceInitializationError(f"Failed to validate Azure AI Inference settings: {e}") from e

        client, model_info = self._create_client(azure_ai_inference_settings)

        super().__init__(
            ai_model_id=model_info.model_name,
            endpoint=azure_ai_inference_settings.endpoint,
            api_key=azure_ai_inference_settings.api_key,
            service_id=service_id or model_info.model_name,
            client=client,
        )

    async def get_chat_message_contents(
        self,
        chat_history: ChatHistory,
        settings: AzureAIInferenceChatPromptExecutionSettings,
        **kwargs: Any,
    ) -> list[ChatMessageContent]:
        """Get chat message contents from the Azure AI Inference service.

        Args:
            chat_history: A list of chats in a chat_history object.
            settings: Settings for the request.
            kwargs: Optional arguments.

        Returns:
            A list of chat message contents.
        """
        response: ChatCompletions = await self.client.complete(
            messages=self._format_chat_history(chat_history),
            model_extras=settings.extra_parameters,
            **settings.prepare_settings_dict(),
        )
        response_metadata = self._get_metadata_from_response(response)

        return [self._create_chat_message_content(response, choice, response_metadata) for choice in response.choices]

    async def get_streaming_chat_message_contents(
        self,
        chat_history: ChatHistory,
        settings: AzureAIInferenceChatPromptExecutionSettings,
        **kwargs: Any,
    ) -> AsyncGenerator[list[StreamingChatMessageContent], Any]:
        """Get streaming chat message contents from the Azure AI Inference service.

        Args:
            chat_history: A list of chats in a chat_history object.
            settings: Settings for the request.
            kwargs: Optional arguments.

        Returns:
            A list of chat message contents.
        """
        response: AsyncStreamingChatCompletions = await self.client.complete(
            stream=True,
            messages=self._format_chat_history(chat_history),
            model_extras=settings.extra_parameters,
            **settings.prepare_settings_dict(),
        )

        async for chunk in response:
            if len(chunk.choices) == 0:
                continue
            chunk_metadata = self._get_metadata_from_response(chunk)
            yield [
                self._create_streaming_chat_message_content(chunk, choice, chunk_metadata) for choice in chunk.choices
            ]

    def _create_client(
        self, azure_ai_inference_settings: AzureAIInferenceSettings
    ) -> tuple[ChatCompletionsClientAsync, ModelInfo]:
        """Create the Azure AI Inference client.

        Client is created synchronously to check the model type before creating the async client.
        """
        chat_completions_client_sync = load_client_sync(
            endpoint=azure_ai_inference_settings.endpoint,
            credential=AzureKeyCredential(azure_ai_inference_settings.api_key.get_secret_value()),
        )

        model_info = chat_completions_client_sync.get_model_info()
        if model_info.model_type not in (ModelType.CHAT, "completion"):
            raise ServiceInitializationError(
                f"Endpoint {azure_ai_inference_settings.endpoint} does not support chat completion."
                f" The provided endpoint is for a {model_info.model_type} model."
            )

        return (
            ChatCompletionsClientAsync(
                endpoint=azure_ai_inference_settings.endpoint,
                credential=AzureKeyCredential(azure_ai_inference_settings.api_key.get_secret_value()),
            ),
            model_info,
        )

    def _get_metadata_from_response(self, response: ChatCompletions | AsyncStreamingChatCompletions) -> dict[str, Any]:
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
            "usage": response.usage,
        }

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
        return ChatMessageContent(
            role=AuthorRole(choice.message.role),
            content=choice.message.content,
            inner_content=response,
            finish_reason=FinishReason(choice.finish_reason),
            metadata=metadata,
        )

    def _create_streaming_chat_message_content(
        self,
        chunk: AsyncStreamingChatCompletions,
        choice: StreamingChatChoiceUpdate,
        metadata: dict[str, Any],
    ) -> StreamingChatMessageContent:
        """Create a streaming chat message content object.

        Args:
            chunk: The chunk from the response.
            choice: The choice from the response.
            metadata: The metadata from the response.

        Returns:
            A streaming chat message content object.
        """
        return StreamingChatMessageContent(
            role=AuthorRole(choice.delta.role),
            content=choice.delta.content,
            choice_index=choice.index,
            inner_content=chunk,
            finish_reason=FinishReason(choice.finish_reason),
            metadata=metadata,
        )

    def _format_chat_history(self, chat_history: ChatHistory) -> list[ChatRequestMessage]:
        """Format the chat history to the expected objects for the client.

        Args:
            chat_history: The chat history.

        Returns:
            A list of formatted chat history.
        """
        self._prepare_chat_history_for_request(chat_history)
        return [MessageConverter[message.role](content=message.content) for message in chat_history.messages]

    def get_prompt_execution_settings_class(
        self,
    ) -> AzureAIInferenceChatPromptExecutionSettings:
        """Get the request settings class."""
        return AzureAIInferenceChatPromptExecutionSettings
