# Copyright (c) Microsoft. All rights reserved.

import json
import logging
import sys
from collections.abc import AsyncGenerator, Callable
from typing import TYPE_CHECKING, Any, ClassVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from anthropic import AsyncAnthropic
from anthropic.lib.streaming._types import TextEvent
from anthropic.types import (
    ContentBlockStopEvent,
    Message,
    MessageDeltaUsage,
    RawMessageDeltaEvent,
    RawMessageStartEvent,
    TextBlock,
    ToolUseBlock,
    Usage,
)
from openai.types.completion_usage import PromptTokensDetails
from pydantic import ValidationError

from semantic_kernel.connectors.ai.anthropic.prompt_execution_settings.anthropic_prompt_execution_settings import (
    AnthropicChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.anthropic.services.utils import (
    MESSAGE_CONVERTERS,
    update_settings_from_function_call_configuration,
)
from semantic_kernel.connectors.ai.anthropic.settings.anthropic_settings import AnthropicSettings
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.completion_usage import CompletionUsage
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceType
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import CMC_ITEM_TYPES, ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.streaming_chat_message_content import STREAMING_CMC_ITEM_TYPES as STREAMING_ITEM_TYPES
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason as SemanticKernelFinishReason
from semantic_kernel.exceptions.service_exceptions import (
    ServiceInitializationError,
    ServiceInvalidRequestError,
    ServiceInvalidResponseError,
    ServiceResponseException,
)
from semantic_kernel.utils.feature_stage_decorator import experimental
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import (
    trace_chat_completion,
    trace_streaming_chat_completion,
)

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration

# map finish reasons from Anthropic to Semantic Kernel
ANTHROPIC_TO_SEMANTIC_KERNEL_FINISH_REASON_MAP = {
    "end_turn": SemanticKernelFinishReason.STOP,
    "stop_sequence": SemanticKernelFinishReason.STOP,
    "max_tokens": SemanticKernelFinishReason.LENGTH,
    "model_context_window_exceeded": SemanticKernelFinishReason.LENGTH,
    "tool_use": SemanticKernelFinishReason.TOOL_CALLS,
    "refusal": SemanticKernelFinishReason.CONTENT_FILTER,
}

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class AnthropicChatCompletion(ChatCompletionClientBase):
    """Anthropic ChatCompletion class."""

    MODEL_PROVIDER_NAME: ClassVar[str] = "anthropic"
    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = True

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
            anthropic_settings = AnthropicSettings(
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
    def _update_function_choice_settings_callback(
        self,
    ) -> Callable[["FunctionCallChoiceConfiguration", "PromptExecutionSettings", FunctionChoiceType], None]:
        return update_settings_from_function_call_configuration

    @override
    def _reset_function_choice_settings(self, settings: "PromptExecutionSettings") -> None:
        if hasattr(settings, "tool_choice"):
            settings.tool_choice = None
        if hasattr(settings, "tools"):
            settings.tools = None

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
        settings.messages, parsed_system_message = self._prepare_chat_history_for_request(chat_history)
        if settings.system is None and parsed_system_message is not None:
            settings.system = parsed_system_message

        return await self._send_chat_request(settings)

    @override
    @trace_streaming_chat_completion(MODEL_PROVIDER_NAME)
    async def _inner_get_streaming_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
        function_invoke_attempt: int = 0,
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
        if not isinstance(settings, AnthropicChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, AnthropicChatPromptExecutionSettings)  # nosec

        settings.messages, parsed_system_message = self._prepare_chat_history_for_request(chat_history, stream=True)
        settings.ai_model_id = settings.ai_model_id or self.ai_model_id
        if settings.system is None and parsed_system_message is not None:
            settings.system = parsed_system_message

        response = self._send_chat_stream_request(settings, function_invoke_attempt)
        if not isinstance(response, AsyncGenerator):
            raise ServiceInvalidResponseError("Expected an AsyncGenerator response.")

        async for message in response:
            yield message

    @override
    def _prepare_chat_history_for_request(
        self,
        chat_history: "ChatHistory",
        role_key: str = "role",
        content_key: str = "content",
        stream: bool = False,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Prepare the chat history for an Anthropic request.

        Allowing customization of the key names for role/author, and optionally overriding the role.

        Args:
            chat_history: The chat history to prepare.
            role_key: The key name for the role/author.
            content_key: The key name for the content/message.
            stream: Whether the request is for a streaming chat.

        Returns:
            A tuple containing the prepared chat history and the first SYSTEM message content.
        """
        system_message_content = None
        system_message_count = 0
        formatted_messages: list[dict[str, Any]] = []
        for i in range(len(chat_history)):
            prev_message = chat_history[i - 1] if i > 0 else None
            curr_message = chat_history[i]
            if curr_message.role == AuthorRole.SYSTEM:
                # Skip system messages after the first one is found
                if system_message_count == 0:
                    system_message_content = curr_message.content
                system_message_count += 1
            elif curr_message.role == AuthorRole.USER or curr_message.role == AuthorRole.ASSISTANT:
                formatted_messages.append(MESSAGE_CONVERTERS[curr_message.role](curr_message))
            elif curr_message.role == AuthorRole.TOOL:
                if prev_message is None:
                    # Under no circumstances should a tool message be the first message in the chat history
                    raise ServiceInvalidRequestError("Tool message found without a preceding message.")
                if prev_message.role == AuthorRole.USER or prev_message.role == AuthorRole.SYSTEM:
                    # A tool message should not be found after a user or system message
                    # Please NOTE that in SK there are the USER role and the TOOL role, but in Anthropic
                    # the tool messages are considered as USER messages. We are checking against the SK roles.
                    raise ServiceInvalidRequestError("Tool message found after a user or system message.")

                formatted_message = MESSAGE_CONVERTERS[curr_message.role](curr_message)
                if prev_message.role == AuthorRole.ASSISTANT:
                    # The first tool message after an assistant message should be a new message
                    formatted_messages.append(formatted_message)
                else:
                    # Append the tool message to the previous tool message.
                    # This indicates that the assistant message requested multiple parallel tool calls.
                    # Anthropic requires that parallel Tool messages are grouped together in a single message.
                    formatted_messages[-1][content_key] += formatted_message[content_key]
            else:
                raise ServiceInvalidRequestError(f"Unsupported role in chat history: {curr_message.role}")

        if system_message_count > 1:
            logger.warning(
                "Anthropic service only supports one system message, but %s system messages were found."
                " Only the first system message will be included in the request.",
                system_message_count,
            )

        return formatted_messages, system_message_content

    # endregion

    def _create_chat_message_content(
        self, response: Message, response_metadata: dict[str, Any]
    ) -> "ChatMessageContent":
        """Create a chat message content object."""
        items: list[CMC_ITEM_TYPES] = []
        items += self._get_tool_calls_from_message(response)

        for content_block in response.content:
            if isinstance(content_block, TextBlock):
                items.append(TextContent(text=content_block.text))

        finish_reason = None
        if response.stop_reason:
            finish_reason = ANTHROPIC_TO_SEMANTIC_KERNEL_FINISH_REASON_MAP.get(response.stop_reason)

        return ChatMessageContent(
            inner_content=response,
            ai_model_id=self.ai_model_id,
            metadata=response_metadata,
            role=AuthorRole.ASSISTANT,
            items=items,
            finish_reason=finish_reason,
        )

    def _create_streaming_chat_message_content(
        self,
        stream_event: TextEvent | ContentBlockStopEvent | RawMessageDeltaEvent,
        metadata: dict[str, Any] | None = None,
        function_invoke_attempt: int = 0,
    ) -> StreamingChatMessageContent:
        """Create a streaming chat message content object from a content block."""
        items: list[STREAMING_ITEM_TYPES] = []
        finish_reason = None

        if isinstance(stream_event, TextEvent):
            items.append(StreamingTextContent(choice_index=0, text=stream_event.text))
        elif (
            isinstance(stream_event, ContentBlockStopEvent)
            and hasattr(stream_event, "content_block")
            and stream_event.content_block.type == "tool_use"
        ):
            tool_use_block = stream_event.content_block
            items.append(
                FunctionCallContent(
                    id=tool_use_block.id,
                    index=stream_event.index,
                    name=tool_use_block.name,
                    arguments=json.dumps(tool_use_block.input) if tool_use_block.input else None,
                )
            )
        elif isinstance(stream_event, RawMessageDeltaEvent):
            finish_reason = ANTHROPIC_TO_SEMANTIC_KERNEL_FINISH_REASON_MAP.get(str(stream_event.delta.stop_reason))
            usage = _get_completion_usage(stream_event.usage)
            start_usage = metadata.get("usage") if metadata else None
            if getattr(stream_event.usage, "input_tokens", None) is None and isinstance(start_usage, CompletionUsage):
                # The input token counts are only reported at message start.
                usage = start_usage.model_copy(update={"completion_tokens": usage.completion_tokens})
            metadata = (metadata or {}) | {"usage": usage}

        return StreamingChatMessageContent(
            choice_index=0,
            inner_content=stream_event,
            ai_model_id=self.ai_model_id,
            metadata=metadata,
            role=AuthorRole.ASSISTANT,
            finish_reason=finish_reason,
            items=items,
            function_invoke_attempt=function_invoke_attempt,
        )

    async def _send_chat_request(self, settings: AnthropicChatPromptExecutionSettings) -> list["ChatMessageContent"]:
        """Send the chat request."""
        try:
            response = await self.async_client.messages.create(**settings.prepare_settings_dict())
        except Exception as ex:
            raise ServiceResponseException(
                f"{type(self)} service failed to complete the request",
                ex,
            ) from ex

        response_metadata: dict[str, Any] = {"id": response.id}
        if hasattr(response, "usage") and response.usage is not None:
            response_metadata["usage"] = _get_completion_usage(response.usage)

        return [self._create_chat_message_content(response, response_metadata)]

    async def _send_chat_stream_request(
        self,
        settings: AnthropicChatPromptExecutionSettings,
        function_invoke_attempt: int = 0,
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], None]:
        """Send the chat stream request.

        The stream yields a sequence of stream events, which are used to create streaming chat message content:
        - RawMessageStartEvent is used to determine the message id and input tokens.
        - RawMessageDeltaEvent is used to determine the finish reason.
        - TextEvent is used to determine the text content and ContentBlockStopEvent is used to determine
            the tool use content.
        """
        try:
            async with self.async_client.messages.stream(**settings.prepare_settings_dict()) as stream:
                metadata: dict[str, Any] = {"usage": None, "id": None}
                async for stream_event in stream:
                    if isinstance(stream_event, RawMessageStartEvent):
                        metadata["usage"] = _get_completion_usage(stream_event.message.usage)
                        metadata["id"] = stream_event.message.id
                    elif isinstance(stream_event, (TextEvent, RawMessageDeltaEvent)) or (
                        isinstance(stream_event, ContentBlockStopEvent)
                        and stream_event.content_block.type == "tool_use"
                    ):
                        yield [
                            self._create_streaming_chat_message_content(stream_event, metadata, function_invoke_attempt)
                        ]
        except Exception as ex:
            raise ServiceResponseException(
                f"{type(self)} service failed to complete the request",
                ex,
            ) from ex

    def _get_tool_calls_from_message(self, message: Message) -> list[FunctionCallContent]:
        """Get tool calls from a content blocks."""
        tool_calls: list[FunctionCallContent] = []

        for idx, content_block in enumerate(message.content):
            if isinstance(content_block, ToolUseBlock):
                tool_calls.append(
                    FunctionCallContent(
                        id=content_block.id,
                        index=idx,
                        name=content_block.name,
                        arguments=getattr(content_block, "input", None),
                    )
                )

        return tool_calls


def _get_completion_usage(usage: Usage | MessageDeltaUsage) -> CompletionUsage:
    """Convert Anthropic usage to CompletionUsage.

    Anthropic reports the tokens read from and written to the prompt cache separately from `input_tokens`,
    so they are added back to get the full prompt token count. Older SDK versions lack some of these fields.
    """
    cache_read_tokens = getattr(usage, "cache_read_input_tokens", None) or 0
    cache_creation_tokens = getattr(usage, "cache_creation_input_tokens", None) or 0
    return CompletionUsage(
        prompt_tokens=(getattr(usage, "input_tokens", None) or 0) + cache_read_tokens + cache_creation_tokens,
        prompt_tokens_details=PromptTokensDetails(cached_tokens=cache_read_tokens) if cache_read_tokens else None,
        completion_tokens=usage.output_tokens,
    )
