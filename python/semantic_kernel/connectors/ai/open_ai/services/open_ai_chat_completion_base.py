# Copyright (c) Microsoft. All rights reserved.

import logging
from copy import copy
from typing import TYPE_CHECKING, Any, AsyncGenerator, Dict, List, Optional, Tuple, Union

from openai import AsyncStream
from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
    OpenAIPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import OpenAIHandler
from semantic_kernel.connectors.ai.open_ai.services.tool_call_behavior import ToolCallBehavior
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.author_role import AuthorRole
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.finish_reason import FinishReason
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.exceptions import (
    FunctionCallInvalidArgumentsException,
    ServiceInvalidExecutionSettingsError,
    ServiceInvalidResponseError,
)
from semantic_kernel.utils.chat import store_results

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)


class OpenAIChatCompletionBase(OpenAIHandler, ChatCompletionClientBase):
    """OpenAI Chat completion class."""

    # region Overriding base class methods
    # most of the methods are overridden from the ChatCompletionClientBase class, otherwise it is mentioned

    # override from AIServiceClientBase
    def get_prompt_execution_settings_class(self) -> "PromptExecutionSettings":
        """Create a request settings object."""
        return OpenAIChatPromptExecutionSettings

    async def complete_chat(
        self,
        chat_history: ChatHistory,
        settings: OpenAIPromptExecutionSettings,
        **kwargs: Any,
    ) -> List["ChatMessageContent"]:
        """Executes a chat completion request and returns the result.

        Arguments:
            chat_history {ChatHistory} -- The chat history to use for the chat completion.
            settings {OpenAIChatPromptExecutionSettings | AzureChatPromptExecutionSettings} -- The settings to use
                for the chat completion request.
            kwargs {Dict[str, Any]} -- The optional arguments.

        Returns:
            List[ChatMessageContent] -- The completion result(s).
        """
        tool_call_behavior = self._get_tool_call_behavior(settings)
        kernel = kwargs.get("kernel", None)
        arguments = kwargs.get("arguments", None)
        if tool_call_behavior.auto_invoke_kernel_functions and (kernel is None or arguments is None):
            raise ServiceInvalidExecutionSettingsError(
                "The kernel argument and arguments are required for OpenAI tool calling."
            )

        for _ in range(tool_call_behavior.max_auto_invoke_attempts):
            settings = self._prepare_settings(settings, chat_history, stream_request=False)
            completions = await self._send_chat_request(settings)
            if not tool_call_behavior.auto_invoke_kernel_functions or all(
                not isinstance(item, FunctionCallContent) for completion in completions for item in completion.items
            ):
                return completions
            await self._process_chat_response_with_tool_call(
                completions=completions, chat_history=chat_history, kernel=kernel, arguments=arguments
            )

    async def complete_chat_stream(
        self,
        chat_history: ChatHistory,
        settings: OpenAIPromptExecutionSettings,
        **kwargs: Any,
    ) -> AsyncGenerator[List[StreamingChatMessageContent], Any]:
        """Executes a streaming chat completion request and returns the result.

        Arguments:
            chat_history {ChatHistory} -- The chat history to use for the chat completion.
            settings {OpenAIChatPromptExecutionSettings | AzureChatPromptExecutionSettings} -- The settings to use
                for the chat completion request.
            kwargs {Dict[str, Any]} -- The optional arguments.

        Yields:
            List[StreamingChatMessageContent] -- A stream of
                StreamingChatMessageContent when using Azure.
        """
        tool_call_behavior = self._get_tool_call_behavior(settings)
        kernel = kwargs.get("kernel", None)
        arguments = kwargs.get("arguments", None)
        if tool_call_behavior.auto_invoke_kernel_functions and (kernel is None or arguments is None):
            raise ServiceInvalidExecutionSettingsError(
                "The kernel argument and arguments are required for OpenAI tool calling."
            )

        for _ in range(tool_call_behavior.max_auto_invoke_attempts):
            settings = self._prepare_settings(settings, chat_history, stream_request=True)
            response = await self._send_chat_stream_request(settings)
            finish_reason = None
            async for content, finish_reason in self._process_chat_stream_response(
                response=response,
                chat_history=chat_history,
                kernel=kernel,
                tool_call_behavior=tool_call_behavior,
                arguments=arguments,
            ):
                if content:
                    yield content
            if finish_reason != FinishReason.TOOL_CALLS:
                break

    def _chat_message_content_to_dict(self, message: "ChatMessageContent") -> Dict[str, Optional[str]]:
        msg = super()._chat_message_content_to_dict(message)
        if message.role == "assistant":
            if tool_calls := getattr(message, "tool_calls", None):
                msg["tool_calls"] = [tool_call.model_dump() for tool_call in tool_calls]
            if function_call := getattr(message, "function_call", None):
                msg["function_call"] = function_call.model_dump_json()
        if message.role == "tool":
            if tool_call_id := getattr(message, "tool_call_id", None):
                msg["tool_call_id"] = tool_call_id
            if message.metadata and "function" in message.metadata:
                msg["name"] = message.metadata["function_name"]
        return msg

    # endregion
    # region internal handlers

    async def _send_chat_request(self, settings: OpenAIChatPromptExecutionSettings) -> List["ChatMessageContent"]:
        """Send the chat request"""
        response = await self._send_request(request_settings=settings)
        response_metadata = self._get_metadata_from_chat_response(response)
        completions = [
            self._create_chat_message_content(response, choice, response_metadata) for choice in response.choices
        ]
        return completions

    async def _send_chat_stream_request(self, settings: OpenAIChatPromptExecutionSettings) -> AsyncStream:
        """Send the chat stream request"""
        response = await self._send_request(request_settings=settings)
        if not isinstance(response, AsyncStream):
            raise ServiceInvalidResponseError("Expected an AsyncStream[ChatCompletionChunk] response.")
        return response

    async def _process_chat_response_with_tool_call(
        self,
        completions: List["ChatMessageContent"],
        chat_history: ChatHistory,
        kernel: "Kernel",
        arguments: "KernelArguments",
    ) -> None:
        """Process the completions in the chat response"""
        for result in completions:
            # An assistant message needs to be followed be a tool call response
            chat_history = store_results(chat_history=chat_history, results=[result])
            await self._process_tool_calls(result, kernel, chat_history, arguments)

    async def _process_chat_stream_response(
        self,
        response: AsyncStream,
        chat_history: ChatHistory,
        tool_call_behavior: ToolCallBehavior,
        kernel: Optional["Kernel"] = None,
        arguments: Optional["KernelArguments"] = None,
    ) -> AsyncGenerator[Tuple[List["StreamingChatMessageContent"], Optional["FinishReason"]], Any]:
        """Process the chat stream response and handle tool calls if applicable."""
        full_content = None
        async for chunk in response:
            if len(chunk.choices) == 0:
                continue

            chunk_metadata = self._get_metadata_from_streaming_chat_response(chunk)
            contents = [
                self._create_streaming_chat_message_content(chunk, choice, chunk_metadata) for choice in chunk.choices
            ]
            if not contents:
                continue
            if not tool_call_behavior.auto_invoke_kernel_functions:
                yield contents, None
                continue

            full_content = contents[0] if full_content is None else full_content + contents[0]
            finish_reason = getattr(full_content, "finish_reason", None)
            if not any(isinstance(item, FunctionCallContent) for item in full_content.items) or finish_reason not in (
                FinishReason.STOP,
                FinishReason.TOOL_CALLS,
                None,
            ):
                yield contents, finish_reason

            if finish_reason == FinishReason.STOP:
                tool_call_behavior.auto_invoke_kernel_functions = False
                break
            if finish_reason == FinishReason.TOOL_CALLS:
                chat_history.add_message(message=full_content)
                await self._process_tool_calls(full_content, kernel, chat_history, arguments)
                yield None, finish_reason

    # endregion
    # region content creation

    def _create_chat_message_content(
        self, response: ChatCompletion, choice: Choice, response_metadata: Dict[str, Any]
    ) -> "ChatMessageContent":
        """Create a chat message content object from a choice."""
        metadata = self._get_metadata_from_chat_choice(choice)
        metadata.update(response_metadata)

        items: list[Any] = self._get_tool_calls_from_chat_choice(choice)
        items.extend(self._get_function_call_from_chat_choice(choice))
        if choice.message.content:
            items.append(TextContent(text=choice.message.content))

        return ChatMessageContent(
            inner_content=response,
            ai_model_id=self.ai_model_id,
            metadata=metadata,
            role=AuthorRole(choice.message.role),
            items=items,
            finish_reason=FinishReason(choice.finish_reason) if choice.finish_reason else None,
        )

    def _create_streaming_chat_message_content(
        self,
        chunk: ChatCompletionChunk,
        choice: ChunkChoice,
        chunk_metadata: Dict[str, Any],
    ) -> StreamingChatMessageContent | None:
        """Create a streaming chat message content object from a choice."""
        metadata = self._get_metadata_from_chat_choice(choice)
        metadata.update(chunk_metadata)

        items: list[Any] = self._get_tool_calls_from_chat_choice(choice)
        items.extend(self._get_function_call_from_chat_choice(choice))
        if choice.delta.content is not None:
            items.append(StreamingTextContent(choice_index=choice.index, text=choice.delta.content))
        return StreamingChatMessageContent(
            choice_index=choice.index,
            inner_content=chunk,
            ai_model_id=self.ai_model_id,
            metadata=metadata,
            role=AuthorRole(choice.delta.role) if choice.delta.role else AuthorRole.ASSISTANT,
            finish_reason=FinishReason(choice.finish_reason) if choice.finish_reason else None,
            items=items,
        )

    def _get_metadata_from_chat_response(self, response: ChatCompletion) -> Dict[str, Any]:
        """Get metadata from a chat response."""
        return {
            "id": response.id,
            "created": response.created,
            "system_fingerprint": response.system_fingerprint,
            "usage": getattr(response, "usage", None),
        }

    def _get_metadata_from_streaming_chat_response(self, response: ChatCompletionChunk) -> Dict[str, Any]:
        """Get metadata from a streaming chat response."""
        return {
            "id": response.id,
            "created": response.created,
            "system_fingerprint": response.system_fingerprint,
        }

    def _get_metadata_from_chat_choice(self, choice: Union[Choice, ChunkChoice]) -> Dict[str, Any]:
        """Get metadata from a chat choice."""
        return {
            "logprobs": getattr(choice, "logprobs", None),
        }

    def _get_tool_calls_from_chat_choice(self, choice: Union[Choice, ChunkChoice]) -> List[FunctionCallContent]:
        """Get tool calls from a chat choice."""
        if isinstance(choice, Choice):
            content = choice.message
        else:
            content = choice.delta
        if content.tool_calls is None:
            return []
        return [
            FunctionCallContent(
                id=tool.id,
                index=getattr(tool, "index", None),
                name=tool.function.name,
                arguments=tool.function.arguments,
            )
            for tool in content.tool_calls
        ]

    def _get_function_call_from_chat_choice(self, choice: Union[Choice, ChunkChoice]) -> List[FunctionCallContent]:
        """Get a function call from a chat choice."""
        if isinstance(choice, Choice):
            content = choice.message
        else:
            content = choice.delta
        if content.function_call is None:
            return []
        return [
            FunctionCallContent(
                id="legacy_function_call", name=content.function_call.name, arguments=content.function_call.arguments
            )
        ]

    def _get_tool_call_behavior(self, execution_settings: OpenAIPromptExecutionSettings) -> ToolCallBehavior:
        """Gets the auto invoke and max iterations settings through ToolCallBehavior."""
        auto_invoke_kernel_functions = False
        max_auto_invoke_attempts = 1
        if isinstance(execution_settings, OpenAIChatPromptExecutionSettings):
            if execution_settings.auto_invoke_kernel_functions is not None:
                auto_invoke_kernel_functions = execution_settings.auto_invoke_kernel_functions
            if auto_invoke_kernel_functions and execution_settings.max_auto_invoke_attempts is not None:
                max_auto_invoke_attempts = (
                    execution_settings.max_auto_invoke_attempts if auto_invoke_kernel_functions else 1
                )

        return ToolCallBehavior(
            auto_invoke_kernel_functions=auto_invoke_kernel_functions, max_auto_invoke_attempts=max_auto_invoke_attempts
        )

    # endregion
    # region request preparation

    def _prepare_settings(
        self,
        settings: OpenAIChatPromptExecutionSettings,
        chat_history: ChatHistory,
        stream_request: bool = False,
    ) -> OpenAIChatPromptExecutionSettings:
        """Prepare the promp execution settings for the chat request."""
        settings.messages = self._prepare_chat_history_for_request(chat_history)
        settings.stream = stream_request
        if not settings.ai_model_id:
            settings.ai_model_id = self.ai_model_id

        # If auto_invoke_kernel_functions is True and num_of_responses > 1 provide a warning
        # that the num_of_responses will be configured to one.
        if settings.auto_invoke_kernel_functions and settings.number_of_responses > 1:
            logger.warning(
                (
                    "Auto invoking functions does not support more than one num_of_response. "
                    "The num_of_responses setting is configured as 1."
                )
            )
            settings.number_of_responses = 1
        return settings

    # endregion
    # region tool calling

    async def _process_tool_calls(
        self,
        result: ChatMessageContent,
        kernel: "Kernel",
        chat_history: ChatHistory,
        arguments: "KernelArguments",
    ) -> None:
        """Processes the tool calls in the result and return it as part of the chat history."""
        logger.info(f"processing {len(result.items)} tool calls")
        args_cloned = copy(arguments)
        for function_call in result.items:
            if not isinstance(function_call, FunctionCallContent):
                continue
            try:
                func_args = function_call.parse_arguments()
                if func_args:
                    args_cloned.update(func_args)
            except FunctionCallInvalidArgumentsException as exc:
                logger.exception(
                    f"Received invalid arguments for function {function_call.name}: {exc}. Trying tool call again."
                )
                frc = FunctionResultContent.from_function_call_content_and_result(
                    function_call_content=function_call,
                    result="The tool call arguments are malformed, please try again.",
                )
                chat_history.add_message(message=frc.to_chat_message_content())
                continue
            logger.info(f"Calling {function_call.name} function with args: {function_call.arguments}")
            try:
                func_result = await kernel.invoke(**function_call.split_name_dict(), arguments=args_cloned)
            except Exception as exc:
                logger.exception(f"Error occurred while invoking function {function_call.name}")
                raise ServiceInvalidResponseError(
                    f"Error occurred while invoking function {function_call.name}"
                ) from exc
            frc = FunctionResultContent.from_function_call_content_and_result(
                function_call_content=function_call, result=func_result
            )
            chat_history.add_message(message=frc.to_chat_message_content())


# endregion
