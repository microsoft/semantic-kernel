# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import AsyncGenerator
from typing import Any

from azure.ai.inference.aio import ChatCompletionsClient
from azure.ai.inference.models import (
    AssistantMessage,
    AsyncStreamingChatCompletions,
    ChatChoice,
    ChatCompletions,
    ChatRequestMessage,
    ImageContentItem,
    ImageDetailLevel,
    ImageUrl,
    StreamingChatChoiceUpdate,
    SystemMessage,
    TextContentItem,
    ToolMessage,
    UserMessage,
)
from azure.core.credentials import AzureKeyCredential
from pydantic import ValidationError

from semantic_kernel.connectors.ai.azure_ai_inference import (
    AzureAIInferenceChatPromptExecutionSettings,
    AzureAIInferenceSettings,
)
from semantic_kernel.connectors.ai.azure_ai_inference.services.azure_ai_inference_base import AzureAIInferenceBase
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError
from semantic_kernel.utils.experimental_decorator import experimental_class

_MESSAGE_CONVERTER: dict[AuthorRole, Any] = {
    AuthorRole.SYSTEM: SystemMessage,
    AuthorRole.USER: UserMessage,
    AuthorRole.ASSISTANT: AssistantMessage,
    AuthorRole.TOOL: ToolMessage,
}

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class AzureAIInferenceChatCompletion(ChatCompletionClientBase, AzureAIInferenceBase):
    """Azure AI Inference Chat Completion Service."""

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
        if not client:
            try:
                azure_ai_inference_settings = AzureAIInferenceSettings.create(
                    api_key=api_key,
                    endpoint=endpoint,
                    env_file_path=env_file_path,
                    env_file_encoding=env_file_encoding,
                )
            except ValidationError as e:
                raise ServiceInitializationError(f"Failed to validate Azure AI Inference settings: {e}") from e

            client = ChatCompletionsClient(
                endpoint=azure_ai_inference_settings.endpoint,
                credential=AzureKeyCredential(azure_ai_inference_settings.api_key.get_secret_value()),
            )

        super().__init__(
            ai_model_id=ai_model_id,
            service_id=service_id or ai_model_id,
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
        items = []
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
        items = []
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
        )

    def _format_chat_history(self, chat_history: ChatHistory) -> list[ChatRequestMessage]:
        """Format the chat history to the expected objects for the client.

        Args:
            chat_history: The chat history.

        Returns:
            A list of formatted chat history.
        """
        chat_request_messages: list[ChatRequestMessage] = []

        for message in chat_history.messages:
            if message.role != AuthorRole.USER or not any(isinstance(item, ImageContent) for item in message.items):
                chat_request_messages.append(_MESSAGE_CONVERTER[message.role](content=message.content))
                continue

            # If it's a user message and there are any image items in the message, we need to create a list of
            # content items, otherwise we need to just pass in the content as a string or it will error.
            contentItems = []
            for item in message.items:
                if isinstance(item, TextContent):
                    contentItems.append(TextContentItem(text=item.text))
                elif isinstance(item, ImageContent) and (item.data_uri or item.uri):
                    contentItems.append(
                        ImageContentItem(
                            image_url=ImageUrl(url=item.data_uri or str(item.uri), detail=ImageDetailLevel.Auto)
                        )
                    )
                else:
                    logger.warning(
                        "Unsupported item type in User message while formatting chat history for Azure AI"
                        f" Inference: {type(item)}"
                    )
            chat_request_messages.append(_MESSAGE_CONVERTER[message.role](content=contentItems))

        return chat_request_messages

    def get_prompt_execution_settings_class(
        self,
    ) -> AzureAIInferenceChatPromptExecutionSettings:
        """Get the request settings class."""
        return AzureAIInferenceChatPromptExecutionSettings
