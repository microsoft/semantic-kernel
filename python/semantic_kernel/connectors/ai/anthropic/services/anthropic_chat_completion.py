# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import AsyncGenerator
from typing import Any

from anthropic import AsyncAnthropic
from anthropic.types import (
    ContentBlockStopEvent,
    Message,
    RawContentBlockDeltaEvent,
    RawMessageDeltaEvent,
    RawMessageStartEvent,
    TextBlock,
)
from pydantic import ValidationError

from semantic_kernel.connectors.ai.anthropic.prompt_execution_settings.anthropic_prompt_execution_settings import (
    AnthropicChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.anthropic.settings.anthropic_settings import AnthropicSettings
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.service_exceptions import (
    ServiceInitializationError,
    ServiceResponseException,
)
from semantic_kernel.utils.experimental_decorator import experimental_class

from .utils import finish_reason_from_anthropic_to_semantic_kernel

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class AnthropicChatCompletion(ChatCompletionClientBase):

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    async_client: AsyncAnthropic
    
    def __init__(
        self,
        ai_model_id: str | None = None,
        service_id: str | None = None,
        api_key: str | None = None,
        async_client: AsyncAnthropic | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize an AnthropicChatCompletion service.

        Args:
            ai_model_id (str): Anthropic model name, see
                https://docs.anthropic.com/en/docs/about-claude/models#model-names
            service_id (str | None): Service ID tied to the execution settings.
            api_key (str | None): The optional API key to use. If provided will override,
                the env vars or .env file value.
            async_client (AsyncAnthropic | None) : An existing client to use. 
            env_file_path (str | None): Use the environment settings file as a fallback
                to environment variables. 
            env_file_encoding (str | None): The encoding of the environment settings file. 
        """
        try:
            anthropic_settings = AnthropicSettings.create(
                api_key=api_key,
                chat_model_id=ai_model_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create Anthropic settings.", ex) from ex
        
        if not anthropic_settings.chat_model_id:
            raise ServiceInitializationError("The Anthropic chat model ID is required.")

        if not async_client:
            async_client = AsyncAnthropic(
                api_key=anthropic_settings.api_key.get_secret_value(),
            )

        super().__init__(
            async_client=async_client,
            service_id=service_id or anthropic_settings.chat_model_id,
            ai_model_id=ai_model_id or anthropic_settings.chat_model_id,
        )

    async def get_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
        **kwargs: Any,
    ) -> list["ChatMessageContent"]: 
        """Executes a chat completion request and returns the result.

        Args:
            chat_history (ChatHistory): The chat history to use for the chat completion.
            settings (PromptExecutionSettings): The settings to use
                for the chat completion request.
            kwargs (Dict[str, Any]): The optional arguments.

        Returns:
            List[ChatMessageContent]: The completion result(s).
        """
        if not isinstance(settings, AnthropicChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, AnthropicChatPromptExecutionSettings)  # nosec

        if not settings.ai_model_id:
            settings.ai_model_id = self.ai_model_id

        settings.messages = self._prepare_chat_history_for_request(chat_history)
        try:
            response = await self.async_client.messages.create(**settings.prepare_settings_dict())
        except Exception as ex:
            raise ServiceResponseException(
                f"{type(self)} service failed to complete the prompt",
                ex,
        ) from ex
        
        self.store_usage(response)

        metadata: dict[str, Any] = {"id": response.id}
        # Check if usage exists and has a value, then add it to the metadata
        if hasattr(response, "usage") and response.usage is not None:
            metadata["usage"] = response.usage

        return [self._create_chat_message_content(response, content_block, metadata) 
                for content_block in response.content]
        
    async def get_streaming_chat_message_contents(
        self,
        chat_history: ChatHistory,
        settings: PromptExecutionSettings, 
        **kwargs: Any,
    ) -> AsyncGenerator[list[StreamingChatMessageContent], Any]: 
        """Executes a streaming chat completion request and returns the result.

        Args:
            chat_history (ChatHistory): The chat history to use for the chat completion.
            settings (PromptExecutionSettings): The settings to use
                for the chat completion request.
            kwargs (Dict[str, Any]): The optional arguments.

        Yields:
            List[StreamingChatMessageContent]: A stream of
                StreamingChatMessageContent.
        """
        if not isinstance(settings, AnthropicChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, AnthropicChatPromptExecutionSettings)  # nosec

        if not settings.ai_model_id:
            settings.ai_model_id = self.ai_model_id

        settings.messages = self._prepare_chat_history_for_request(chat_history)
        try:
            async with self.async_client.messages.stream(**settings.prepare_settings_dict()) as stream:
                author_role = None
                metadata: dict[str, Any] = {"usage": {}, "id": None}
                content_block_idx = 0
                
                async for stream_event in stream:
                    if isinstance(stream_event, RawMessageStartEvent):
                        author_role = stream_event.message.role
                        metadata["usage"]["input_tokens"] = stream_event.message.usage.input_tokens
                        metadata["id"] = stream_event.message.id
                    elif isinstance(stream_event, (RawContentBlockDeltaEvent, RawMessageDeltaEvent)):
                        yield [self._create_streaming_chat_message_content(stream_event, 
                                                                           content_block_idx, 
                                                                           author_role, 
                                                                           metadata)]
                    elif isinstance(stream_event, ContentBlockStopEvent):
                        content_block_idx += 1

        except Exception as ex:
            raise ServiceResponseException(
                f"{type(self)} service failed to complete the request",
                ex,
            ) from ex

    def _create_chat_message_content(self, 
                                     response: Message, 
                                     content: TextBlock, 
                                     response_metadata: dict[str, Any]) -> "ChatMessageContent":
        """Create a chat message content object."""
        items: list[Any] = []
        
        if content.text:
            items.append(TextContent(text=content.text))

        finish_reason = finish_reason_from_anthropic_to_semantic_kernel(response.stop_reason)
        return ChatMessageContent(
            inner_content=response,
            ai_model_id=self.ai_model_id,
            metadata=response_metadata,
            role=AuthorRole(response.role),
            items=items,
            finish_reason=finish_reason,
        )

    def _create_streaming_chat_message_content(self, 
                                               stream_event: RawContentBlockDeltaEvent | RawMessageDeltaEvent,
                                               content_block_idx: int,
                                               role: str | None = None,
                                               metadata: dict[str, Any] = {}) -> StreamingChatMessageContent:
        """Create a streaming chat message content object from a choice."""
        text_content = ""
            
        if stream_event.delta and hasattr(stream_event.delta, "text"):
            text_content = stream_event.delta.text
        
        items: list[Any] = [StreamingTextContent(choice_index=content_block_idx, text=text_content)]
        finish_reason = None

        if isinstance(stream_event, RawMessageDeltaEvent):
            finish_reason = finish_reason_from_anthropic_to_semantic_kernel(stream_event.delta.stop_reason)
            metadata["usage"]["output_tokens"] = stream_event.usage.output_tokens

        return StreamingChatMessageContent(
            choice_index=content_block_idx,
            inner_content=stream_event,
            ai_model_id=self.ai_model_id,
            metadata=metadata,
            role=AuthorRole(role) if role else AuthorRole.ASSISTANT,
            finish_reason=finish_reason,
            items=items,
        )

    def get_prompt_execution_settings_class(self) -> "type[AnthropicChatPromptExecutionSettings]":
        """Create a request settings object."""
        return AnthropicChatPromptExecutionSettings
    
    def store_usage(self, response):
        """Store the usage information from the response."""
        if not isinstance(response, AsyncGenerator):
            logger.info(f"Anthropic usage: {response.usage}")
            self.input_tokens += response.usage.input_tokens
            self.output_tokens += response.usage.output_tokens
