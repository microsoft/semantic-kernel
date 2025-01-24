# Copyright (c) Microsoft. All rights reserved.

import sys
from collections.abc import AsyncGenerator, Callable
from typing import TYPE_CHECKING, Any, ClassVar, cast

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from openai import AsyncStream
from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk, ChoiceDeltaFunctionCall, ChoiceDeltaToolCall
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice
from openai.types.chat.chat_completion_message import FunctionCall
from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall
from typing_extensions import deprecated

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.completion_usage import CompletionUsage
from semantic_kernel.connectors.ai.function_calling_utils import update_settings_from_function_call_configuration
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior, FunctionChoiceType
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import OpenAIHandler
from semantic_kernel.contents.annotation_content import AnnotationContent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.file_reference_content import FileReferenceContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.exceptions import ServiceInvalidExecutionSettingsError, ServiceInvalidResponseError
from semantic_kernel.filters.auto_function_invocation.auto_function_invocation_context import (
    AutoFunctionInvocationContext,
)
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import (
    trace_chat_completion,
    trace_streaming_chat_completion,
)

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.kernel import Kernel


class OpenAIChatCompletionBase(OpenAIHandler, ChatCompletionClientBase):
    """OpenAI Chat completion class."""

    MODEL_PROVIDER_NAME: ClassVar[str] = "openai"
    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = True

    # region Overriding base class methods
    # most of the methods are overridden from the ChatCompletionClientBase class, otherwise it is mentioned

    # Override from AIServiceClientBase
    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        return OpenAIChatPromptExecutionSettings

    # Override from AIServiceClientBase
    @override
    def service_url(self) -> str | None:
        return str(self.client.base_url)

    @override
    @trace_chat_completion(MODEL_PROVIDER_NAME)
    async def _inner_get_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> list["ChatMessageContent"]:
        if not isinstance(settings, OpenAIChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, OpenAIChatPromptExecutionSettings)  # nosec

        settings.stream = False
        settings.messages = self._prepare_chat_history_for_request(chat_history)
        settings.ai_model_id = settings.ai_model_id or self.ai_model_id

        response = await self._send_request(settings)
        assert isinstance(response, ChatCompletion)  # nosec
        response_metadata = self._get_metadata_from_chat_response(response)
        return [self._create_chat_message_content(response, choice, response_metadata) for choice in response.choices]

    @override
    @trace_streaming_chat_completion(MODEL_PROVIDER_NAME)
    async def _inner_get_streaming_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
        function_invoke_attempt: int = 0,
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
        if not isinstance(settings, OpenAIChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, OpenAIChatPromptExecutionSettings)  # nosec

        settings.stream = True
        settings.stream_options = {"include_usage": True}
        settings.messages = self._prepare_chat_history_for_request(chat_history)
        settings.ai_model_id = settings.ai_model_id or self.ai_model_id

        response = await self._send_request(settings)
        if not isinstance(response, AsyncStream):
            raise ServiceInvalidResponseError("Expected an AsyncStream[ChatCompletionChunk] response.")
        async for chunk in response:
            if len(chunk.choices) == 0 and chunk.usage is None:
                continue

            assert isinstance(chunk, ChatCompletionChunk)  # nosec
            chunk_metadata = self._get_metadata_from_streaming_chat_response(chunk)
            if chunk.usage is not None:
                # Usage is contained in the last chunk where the choices are empty
                # We are duplicating the usage metadata to all the choices in the response
                yield [
                    StreamingChatMessageContent(
                        role=AuthorRole.ASSISTANT,
                        content="",
                        choice_index=i,
                        inner_content=chunk,
                        ai_model_id=settings.ai_model_id,
                        metadata=chunk_metadata,
                        function_invoke_attempt=function_invoke_attempt,
                    )
                    for i in range(settings.number_of_responses or 1)
                ]
            else:
                yield [
                    self._create_streaming_chat_message_content(chunk, choice, chunk_metadata, function_invoke_attempt)
                    for choice in chunk.choices
                ]

    @override
    def _verify_function_choice_settings(self, settings: "PromptExecutionSettings") -> None:
        if not isinstance(settings, OpenAIChatPromptExecutionSettings):
            raise ServiceInvalidExecutionSettingsError("The settings must be an OpenAIChatPromptExecutionSettings.")
        if settings.number_of_responses is not None and settings.number_of_responses > 1:
            raise ServiceInvalidExecutionSettingsError(
                "Auto-invocation of tool calls may only be used with a "
                "OpenAIChatPromptExecutions.number_of_responses of 1."
            )

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

    # endregion

    # region content creation

    def _create_chat_message_content(
        self, response: ChatCompletion, choice: Choice, response_metadata: dict[str, Any]
    ) -> "ChatMessageContent":
        """Create a chat message content object from a choice."""
        metadata = self._get_metadata_from_chat_choice(choice)
        metadata.update(response_metadata)

        items: list[Any] = self._get_tool_calls_from_chat_choice(choice)
        items.extend(self._get_function_call_from_chat_choice(choice))
        if choice.message.content:
            items.append(TextContent(text=choice.message.content))
        elif hasattr(choice.message, "refusal") and choice.message.refusal:
            items.append(TextContent(text=choice.message.refusal))

        return ChatMessageContent(
            inner_content=response,
            ai_model_id=self.ai_model_id,
            metadata=metadata,
            role=AuthorRole(choice.message.role),
            items=items,
            finish_reason=(FinishReason(choice.finish_reason) if choice.finish_reason else None),
        )

    def _create_streaming_chat_message_content(
        self,
        chunk: ChatCompletionChunk,
        choice: ChunkChoice,
        chunk_metadata: dict[str, Any],
        function_invoke_attempt: int,
    ) -> StreamingChatMessageContent:
        """Create a streaming chat message content object from a choice."""
        metadata = self._get_metadata_from_chat_choice(choice)
        metadata.update(chunk_metadata)

        items: list[Any] = self._get_tool_calls_from_chat_choice(choice)
        items.extend(self._get_function_call_from_chat_choice(choice))
        if choice.delta and choice.delta.content is not None:
            items.append(StreamingTextContent(choice_index=choice.index, text=choice.delta.content))
        return StreamingChatMessageContent(
            choice_index=choice.index,
            inner_content=chunk,
            ai_model_id=self.ai_model_id,
            metadata=metadata,
            role=(AuthorRole(choice.delta.role) if choice.delta and choice.delta.role else AuthorRole.ASSISTANT),
            finish_reason=(FinishReason(choice.finish_reason) if choice.finish_reason else None),
            items=items,
            function_invoke_attempt=function_invoke_attempt,
        )

    def _get_metadata_from_chat_response(self, response: ChatCompletion) -> dict[str, Any]:
        """Get metadata from a chat response."""
        return {
            "id": response.id,
            "created": response.created,
            "system_fingerprint": response.system_fingerprint,
            "usage": CompletionUsage.from_openai(response.usage) if response.usage is not None else None,
        }

    def _get_metadata_from_streaming_chat_response(self, response: ChatCompletionChunk) -> dict[str, Any]:
        """Get metadata from a streaming chat response."""
        return {
            "id": response.id,
            "created": response.created,
            "system_fingerprint": response.system_fingerprint,
            "usage": CompletionUsage.from_openai(response.usage) if response.usage is not None else None,
        }

    def _get_metadata_from_chat_choice(self, choice: Choice | ChunkChoice) -> dict[str, Any]:
        """Get metadata from a chat choice."""
        return {
            "logprobs": getattr(choice, "logprobs", None),
        }

    def _get_tool_calls_from_chat_choice(self, choice: Choice | ChunkChoice) -> list[FunctionCallContent]:
        """Get tool calls from a chat choice."""
        content = choice.message if isinstance(choice, Choice) else choice.delta
        if content and (tool_calls := getattr(content, "tool_calls", None)) is not None:
            return [
                FunctionCallContent(
                    id=tool.id,
                    index=getattr(tool, "index", None),
                    name=tool.function.name,
                    arguments=tool.function.arguments,
                )
                for tool in cast(list[ChatCompletionMessageToolCall] | list[ChoiceDeltaToolCall], tool_calls)
                if tool.function is not None
            ]
        # When you enable asynchronous content filtering in Azure OpenAI, you may receive empty deltas
        return []

    def _get_function_call_from_chat_choice(self, choice: Choice | ChunkChoice) -> list[FunctionCallContent]:
        """Get a function call from a chat choice."""
        content = choice.message if isinstance(choice, Choice) else choice.delta
        if content and (function_call := getattr(content, "function_call", None)) is not None:
            function_call = cast(FunctionCall | ChoiceDeltaFunctionCall, function_call)
            return [
                FunctionCallContent(
                    id="legacy_function_call", name=function_call.name, arguments=function_call.arguments
                )
            ]
        # When you enable asynchronous content filtering in Azure OpenAI, you may receive empty deltas
        return []

    def _prepare_chat_history_for_request(
        self,
        chat_history: "ChatHistory",
        role_key: str = "role",
        content_key: str = "content",
    ) -> Any:
        """Prepare the chat history for a request.

        Allowing customization of the key names for role/author, and optionally overriding the role.

        ChatRole.TOOL messages need to be formatted different than system/user/assistant messages:
            They require a "tool_call_id" and (function) "name" key, and the "metadata" key should
            be removed. The "encoding" key should also be removed.

        Override this method to customize the formatting of the chat history for a request.

        Args:
            chat_history (ChatHistory): The chat history to prepare.
            role_key (str): The key name for the role/author.
            content_key (str): The key name for the content/message.

        Returns:
            prepared_chat_history (Any): The prepared chat history for a request.
        """
        return [
            {
                **message.to_dict(role_key=role_key, content_key=content_key),
                role_key: "developer"
                if self.instruction_role == "developer" and message.to_dict(role_key=role_key)[role_key] == "system"
                else message.to_dict(role_key=role_key)[role_key],
            }
            for message in chat_history.messages
            if not isinstance(message, (AnnotationContent, FileReferenceContent))
        ]

    # endregion

    # region function calling
    @deprecated("Use `invoke_function_call` from the kernel instead with `FunctionChoiceBehavior`.")
    async def _process_function_call(
        self,
        function_call: FunctionCallContent,
        chat_history: ChatHistory,
        kernel: "Kernel",
        arguments: "KernelArguments | None",
        function_call_count: int,
        request_index: int,
        function_call_behavior: FunctionChoiceBehavior,
    ) -> "AutoFunctionInvocationContext | None":
        """Processes the tool calls in the result and update the chat history."""
        return await kernel.invoke_function_call(
            function_call=function_call,
            chat_history=chat_history,
            arguments=arguments,
            function_call_count=function_call_count,
            request_index=request_index,
            function_behavior=function_call_behavior,
        )

    # endregion
