# Copyright (c) Microsoft. All rights reserved.

import sys
from collections.abc import AsyncGenerator, Callable
from typing import TYPE_CHECKING, Any, ClassVar, cast

from semantic_kernel.connectors.ai.response_usage import ResponseUsage
from semantic_kernel.contents.response_function_result_content import ResponseFunctionResultContent
from semantic_kernel.contents.utils.status import Status

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from openai import AsyncStream
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice
from openai.types.responses import ResponseFunctionToolCall
from openai.types.responses.response import Response
from openai.types.responses.response_function_call_arguments_delta_event import ResponseFunctionCallArgumentsDeltaEvent
from openai.types.responses.response_output_message import ResponseOutputMessage
from openai.types.responses.response_output_text import ResponseOutputText
from typing_extensions import deprecated

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.function_calling_utils import update_settings_from_function_call_configuration
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior, FunctionChoiceType
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import OpenAIHandler
from semantic_kernel.contents.annotation_content import AnnotationContent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.file_reference_content import FileReferenceContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.response_message_content import ResponseMessageContent
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


class OpenAIResponseBase(OpenAIHandler, ChatCompletionClientBase):
    """OpenAI Response Base class."""

    MODEL_PROVIDER_NAME: ClassVar[str] = "openai"
    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = True

    # region Overriding base class methods
    # most of the methods are overridden from the ChatCompletionClientBase class, otherwise it is mentioned

    # Override from AIServiceClientBase
    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        pass

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
    ) -> list["ResponseMessageContent"]:
        if not isinstance(settings, PromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, PromptExecutionSettings)  # nosec

        settings.stream = False
        settings.messages = self._prepare_chat_history_for_request(chat_history)
        settings.ai_model_id = settings.ai_model_id or self.ai_model_id

        response = await self._send_request(settings)
        assert isinstance(response, Response)  # nosec
        response_metadata = self._get_metadata_from_response(response)
        return [self._create_response_message_content(response, response_metadata)]

    @override
    @trace_streaming_chat_completion(MODEL_PROVIDER_NAME)
    async def _inner_get_streaming_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
        function_invoke_attempt: int = 0,
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
        if not isinstance(settings, PromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, PromptExecutionSettings)  # nosec

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
        if not isinstance(settings, PromptExecutionSettings):
            raise ServiceInvalidExecutionSettingsError("The settings must be an OpenAIResponseExecutionSettings.")

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

    # def _create_response_message_content(
    #     self, response: Response, response_metadata: dict[str, Any]
    # ) -> "ResponseMessageContent":
    #     """Create a chat message content object from a choice."""
    #     metadata = self._get_metadata_from_output(response.output)
    #     metadata.update(response_metadata)

    #     items: list[Any] = self._get_tool_calls_from_output(response.output)
    #     if response.output and any(isinstance(item, ResponseOutputMessage) for item in response.output):
    #         for item in response.output:
    #             # TODO(evmattso): handle other output types
    #             if not isinstance(item, ResponseOutputMessage):
    #                 continue
    #             for c in item.content:
    #                 if isinstance(c, ResponseOutputText):
    #                     items.append(TextContent(text=c.text))
    #                     if c.annotations:
    #                         for ann in c.annotations:
    #                             items.append(AnnotationContent(**ann.model_dump()))
    #     # TODO(evmattso): handle refusals?

    #     return ResponseMessageContent(
    #         inner_content=response,
    #         ai_model_id=self.ai_model_id,
    #         metadata=metadata,
    #         role=AuthorRole(response.output[0].role if hasattr(response.output[0], "role") else "assistant"),
    #         items=items,
    #         status=Status(response.status),
    #     )

    def _create_response_message_content(
        self, response: Response, response_metadata: dict[str, Any]
    ) -> "ResponseMessageContent":
        """Create a chat message content object from a choice."""
        metadata = self._get_metadata_from_output(response.output)
        metadata.update(response_metadata)

        # Collect all items (tool calls, text content, annotations) into a single list
        items = self._collect_items_from_output(response.output)

        # Determine role (if none is found, default to 'assistant')
        role_str = response.output[0].role if (response.output and hasattr(response.output[0], "role")) else "assistant"

        return ResponseMessageContent(
            inner_content=response,
            ai_model_id=self.ai_model_id,
            metadata=metadata,
            role=AuthorRole(role_str),
            items=items,
            status=Status(response.status),
        )

    def _collect_items_from_output(self, output: list[Any]) -> list[Any]:
        """Aggregate items from the various output types."""
        items = []
        items.extend(self._get_tool_calls_from_output(output))

        for msg in filter(lambda output_msg: isinstance(output_msg, ResponseOutputMessage), output or []):
            items.extend(self._collect_text_and_annotations(msg.content))

        return items

    def _collect_text_and_annotations(self, content_list: list[Any]) -> list[Any]:
        """Collect text content and annotation content from a single message's content."""
        collected = []
        for content in content_list:
            if isinstance(content, ResponseOutputText):
                collected.append(TextContent(text=content.text))
                if content.annotations:
                    for annotation in content.annotations:
                        collected.append(AnnotationContent(**annotation.model_dump()))
        return collected

    def _create_streaming_chat_message_content(
        self,
        chunk: ChatCompletionChunk,
        choice: ChunkChoice,
        chunk_metadata: dict[str, Any],
        function_invoke_attempt: int,
    ) -> StreamingChatMessageContent:
        """Create a streaming chat message content object from a choice."""
        metadata = self._get_metadata_from_output(choice)
        metadata.update(chunk_metadata)

        items: list[Any] = self._get_tool_calls_from_output(choice)
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

    def _get_metadata_from_response(self, response: Response) -> dict[str, Any]:
        """Get metadata from a chat response."""
        return {
            "id": response.id,
            "created": response.created_at,
            "usage": response.usage.model_dump() if response.usage is not None else None,
        }

    def _get_metadata_from_streaming_chat_response(self, response: ChatCompletionChunk) -> dict[str, Any]:
        """Get metadata from a streaming chat response."""
        return {
            "id": response.id,
            "created": response.created,
            "usage": ResponseUsage(**response.usage) if response.usage is not None else None,
        }

    def _get_metadata_from_output(self, output) -> dict[str, Any]:
        """Get metadata from a chat choice."""
        return {
            "metadata": getattr(output, "metadata", None),
        }

    def _get_tool_calls_from_output(
        self, output: ResponseFunctionToolCall | ResponseFunctionCallArgumentsDeltaEvent
    ) -> list[FunctionCallContent]:
        """Get tool calls from a response output."""
        fccs: list[FunctionCallContent] = []
        if not any(isinstance(i, (ResponseFunctionToolCall, ResponseFunctionCallArgumentsDeltaEvent)) for i in output):
            return []
        for tool in cast(list[ResponseFunctionToolCall] | list[ResponseFunctionCallArgumentsDeltaEvent], output):
            content = tool if isinstance(tool, ResponseFunctionToolCall) else tool.delta
            fccs.append(
                FunctionCallContent(
                    id=content.id,
                    call_id=content.call_id,
                    index=getattr(content, "index", None),
                    name=content.name,
                    arguments=content.arguments,
                )
            )
        return fccs

    def _prepare_chat_history_for_request(
        self,
        chat_history: "ChatHistory",
        role_key: str = "role",
        content_key: str = "content",
    ) -> Any:
        """Prepare the chat history for a request into new Responses format."""
        result = []
        for message in chat_history.messages:
            if isinstance(message, (AnnotationContent, FileReferenceContent)):
                continue
            d = message.to_dict(role_key=role_key, content_key=content_key)
            r = d.get(role_key)
            if r == "assistant" and any(isinstance(i, FunctionCallContent) for i in message.items):
                for item in message.items:
                    if isinstance(item, FunctionCallContent):
                        fc_dict = {
                            "type": "function_call",
                            "id": item.id,
                            "call_id": item.call_id,
                            "name": item.name,
                            "arguments": item.arguments,
                        }
                        result.append(fc_dict)
            elif r == "tool" and any(isinstance(i, ResponseFunctionResultContent) for i in message.items):
                for item in message.items:
                    if isinstance(item, ResponseFunctionResultContent):
                        fco_dict = {
                            "type": "function_call_output",
                            "output": str(item.result),
                            "call_id": item.id or "",
                        }
                        result.append(fco_dict)
            else:
                d.pop("tool_calls", None)
                result.append(d)
        return result

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
