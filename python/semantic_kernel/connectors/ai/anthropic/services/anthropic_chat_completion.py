# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import AsyncGenerator
from typing import Any, ClassVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from anthropic import AsyncAnthropic
from anthropic.types import (
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
from semantic_kernel.connectors.ai.completion_usage import CompletionUsage
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ITEM_TYPES, ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import ITEM_TYPES as STREAMING_ITEM_TYPES
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason as SemanticKernelFinishReason
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError, ServiceResponseException
from semantic_kernel.utils.experimental_decorator import experimental_class
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import (
    trace_chat_completion,
    trace_streaming_chat_completion,
)

# map finish reasons from Anthropic to Semantic Kernel
ANTHROPIC_TO_SEMANTIC_KERNEL_FINISH_REASON_MAP = {
    "end_turn": SemanticKernelFinishReason.STOP,
    "max_tokens": SemanticKernelFinishReason.LENGTH,
    "tool_use": SemanticKernelFinishReason.TOOL_CALLS,
}

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class AnthropicChatCompletion(ChatCompletionClientBase):
    """Antropic ChatCompletion class."""

    MODEL_PROVIDER_NAME: ClassVar[str] = "anthropic"
    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = False

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
            ai_model_id: Anthropic model name, see
                https://docs.anthropic.com/en/docs/about-claude/models#model-names
            service_id: Service ID tied to the execution settings.
            api_key: The optional API key to use. If provided will override,
                the env vars or .env file value.
            async_client: An existing client to use.
            env_file_path: Use the environment settings file as a fallback
                to environment variables.
            env_file_encoding: The encoding of the environment settings file.
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
            ai_model_id=anthropic_settings.chat_model_id,
        )

    # region Overriding base class methods

    # Override from AIServiceClientBase
    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        return AnthropicChatPromptExecutionSettings

    # Override from AIServiceClientBase
    @override
    def service_url(self) -> str | None:
        return str(self.async_client.base_url)

    @override
    @trace_chat_completion(MODEL_PROVIDER_NAME)
    async def _inner_get_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> list["ChatMessageContent"]:
        if not isinstance(settings, AnthropicChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, AnthropicChatPromptExecutionSettings)  # nosec

        settings.ai_model_id = settings.ai_model_id or self.ai_model_id
        messages, parsed_system_message = self._prepare_chat_history_for_request(chat_history)
        settings.messages = messages
        if settings.system is None and parsed_system_message is not None:
            settings.system = parsed_system_message
        try:
            response = await self.async_client.messages.create(**settings.prepare_settings_dict())
        except Exception as ex:
            raise ServiceResponseException(
                f"{type(self)} service failed to complete the prompt",
                ex,
            ) from ex

        metadata: dict[str, Any] = {"id": response.id}
        # Check if usage exists and has a value, then add it to the metadata
        if hasattr(response, "usage") and response.usage is not None:
            metadata["usage"] = CompletionUsage(
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
            )

        return [
            self._create_chat_message_content(response, content_block, metadata) for content_block in response.content
        ]

    @override
    @trace_streaming_chat_completion(MODEL_PROVIDER_NAME)
    async def _inner_get_streaming_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
        if not isinstance(settings, AnthropicChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, AnthropicChatPromptExecutionSettings)  # nosec

        settings.ai_model_id = settings.ai_model_id or self.ai_model_id
        messages, parsed_system_message = self._prepare_chat_history_for_request(chat_history)
        settings.messages = messages
        if settings.system is None and parsed_system_message is not None:
            settings.system = parsed_system_message
        try:
            async with self.async_client.messages.stream(**settings.prepare_settings_dict()) as stream:
                author_role = None
                metadata: dict[str, Any] = {"usage": CompletionUsage(), "id": None}
                content_block_idx = 0

                async for stream_event in stream:
                    if isinstance(stream_event, RawMessageStartEvent):
                        author_role = stream_event.message.role
                        metadata["usage"].prompt_tokens = stream_event.message.usage.input_tokens
                        metadata["id"] = stream_event.message.id

                    elif isinstance(stream_event, (RawContentBlockDeltaEvent, RawMessageDeltaEvent)):
                        if hasattr(stream_event, "index") and stream_event.index is not None:
                            content_block_idx = stream_event.index
                        yield [
                            self._create_streaming_chat_message_content(
                                stream_event, content_block_idx, author_role, metadata
                            )
                        ]
        except Exception as ex:
            raise ServiceResponseException(
                f"{type(self)} service failed to complete the request",
                ex,
            ) from ex

    def _prepare_chat_history_for_request(
        self,
        chat_history: "ChatHistory",
        role_key: str = "role",
        content_key: str = "content",
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Prepare the chat history for an Anthropic request.

        Allowing customization of the key names for role/author, and optionally overriding the role.

        Args:
            chat_history: The chat history to prepare.
            role_key: The key name for the role/author.
            content_key: The key name for the content/message.

        Returns:
            A tuple containing the prepared chat history and the first SYSTEM message content.
        """
        system_message_content = None
        remaining_messages = []

        system_message_found = False
        for message in chat_history.messages:
            # Skip system messages after the first one is found
            if message.role == AuthorRole.SYSTEM:
                if not system_message_found:
                    system_message_content = message.content
                    system_message_found = True
                continue

            # The API requires only role and content keys for the remaining messages
            remaining_messages.append({
                role_key: getattr(message, role_key),
                content_key: getattr(message, content_key),
            })

        return remaining_messages, system_message_content

    # endregion

    def _create_chat_message_content(
        self, response: Message, content: TextBlock, response_metadata: dict[str, Any]
    ) -> "ChatMessageContent":
        """Create a chat message content object."""
        items: list[ITEM_TYPES] = []

        if content.text:
            items.append(TextContent(text=content.text))

        finish_reason = None
        if response.stop_reason:
            finish_reason = ANTHROPIC_TO_SEMANTIC_KERNEL_FINISH_REASON_MAP[response.stop_reason]

        return ChatMessageContent(
            inner_content=response,
            ai_model_id=self.ai_model_id,
            metadata=response_metadata,
            role=AuthorRole(response.role),
            items=items,
            finish_reason=finish_reason,
        )

    def _create_streaming_chat_message_content(
        self,
        stream_event: RawContentBlockDeltaEvent | RawMessageDeltaEvent,
        content_block_idx: int,
        role: str | None = None,
        metadata: dict[str, Any] = {},
    ) -> StreamingChatMessageContent:
        """Create a streaming chat message content object from a choice."""
        text_content = ""

        if stream_event.delta and hasattr(stream_event.delta, "text"):
            text_content = stream_event.delta.text

        items: list[STREAMING_ITEM_TYPES] = [StreamingTextContent(choice_index=content_block_idx, text=text_content)]

        finish_reason = None
        if isinstance(stream_event, RawMessageDeltaEvent):
            if stream_event.delta.stop_reason:
                finish_reason = ANTHROPIC_TO_SEMANTIC_KERNEL_FINISH_REASON_MAP[stream_event.delta.stop_reason]

            metadata["usage"].completion_tokens = stream_event.usage.output_tokens

        return StreamingChatMessageContent(
            choice_index=content_block_idx,
            inner_content=stream_event,
            ai_model_id=self.ai_model_id,
            metadata=metadata,
            role=AuthorRole(role) if role else AuthorRole.ASSISTANT,
            finish_reason=finish_reason,
            items=items,
        )
