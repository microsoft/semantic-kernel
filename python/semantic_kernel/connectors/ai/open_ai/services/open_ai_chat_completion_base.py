# Copyright (c) Microsoft. All rights reserved.

import logging
from copy import copy
from typing import TYPE_CHECKING, Any, AsyncIterable, Dict, List, Optional, Tuple, Type, Union

from openai import AsyncStream
from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai.contents import OpenAIChatMessageContent, OpenAIStreamingChatMessageContent
from semantic_kernel.connectors.ai.open_ai.contents.function_call import FunctionCall
from semantic_kernel.connectors.ai.open_ai.contents.tool_calls import ToolCall
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
    OpenAIPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import OpenAIHandler
from semantic_kernel.connectors.ai.open_ai.services.tool_call_behavior import ToolCallBehavior
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.chat_role import ChatRole
from semantic_kernel.contents.finish_reason import FinishReason
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

    def get_chat_message_content_class(self) -> Type[ChatMessageContent]:
        """Get the chat message content types used by a class, default is ChatMessageContent."""
        return OpenAIChatMessageContent

    async def complete_chat(
        self,
        chat_history: ChatHistory,
        settings: OpenAIPromptExecutionSettings,
        **kwargs: Any,
    ) -> List[OpenAIChatMessageContent]:
        """Executes a chat completion request and returns the result.

        Arguments:
            chat_history {ChatHistory} -- The chat history to use for the chat completion.
            settings {OpenAIChatPromptExecutionSettings | AzureChatPromptExecutionSettings} -- The settings to use
                for the chat completion request.
            kwargs {Dict[str, Any]} -- The optional arguments.

        Returns:
            List[OpenAIChatMessageContent | AzureChatMessageContent] -- The completion result(s).
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
            if self._should_return_completions_response(completions=completions, tool_call_behavior=tool_call_behavior):
                return completions
            await self._process_chat_response_with_tool_call(
                completions=completions, chat_history=chat_history, kernel=kernel, arguments=arguments
            )

    async def complete_chat_stream(
        self,
        chat_history: ChatHistory,
        settings: OpenAIPromptExecutionSettings,
        **kwargs: Any,
    ) -> AsyncIterable[List[OpenAIStreamingChatMessageContent]]:
        """Executes a streaming chat completion request and returns the result.

        Arguments:
            chat_history {ChatHistory} -- The chat history to use for the chat completion.
            settings {OpenAIChatPromptExecutionSettings | AzureChatPromptExecutionSettings} -- The settings to use
                for the chat completion request.
            kwargs {Dict[str, Any]} -- The optional arguments.

        Yields:
            List[OpenAIStreamingChatMessageContent | AzureStreamingChatMessageContent] -- A stream of
                OpenAIStreamingChatMessages or AzureStreamingChatMessageContent when using Azure.
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
                yield content
            if finish_reason != FinishReason.TOOL_CALLS:
                break

    def _chat_message_content_to_dict(self, message: ChatMessageContent) -> Dict[str, Optional[str]]:
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

    async def _send_chat_request(self, settings: OpenAIChatPromptExecutionSettings) -> List[OpenAIChatMessageContent]:
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
        completions: List[OpenAIChatMessageContent],
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
    ) -> AsyncIterable[Tuple[List[OpenAIStreamingChatMessageContent], Optional[FinishReason]]]:
        """Process the chat stream response and handle tool calls if applicable."""
        full_content = None
        async for chunk in response:
            if len(chunk.choices) == 0:
                continue

            chunk_metadata = self._get_metadata_from_streaming_chat_response(chunk)
            contents = [
                self._create_streaming_chat_message_content(chunk, choice, chunk_metadata) for choice in chunk.choices
            ]
            if not tool_call_behavior.auto_invoke_kernel_functions:
                yield contents, None
                continue
            finish_reason = getattr(contents[0], "finish_reason", None)
            full_content = contents[0] if full_content is None else full_content + contents[0]
            if not contents[0].tool_calls or finish_reason not in (FinishReason.STOP, FinishReason.TOOL_CALLS, None):
                yield contents, finish_reason

            if finish_reason == FinishReason.STOP:
                tool_call_behavior.auto_invoke_kernel_functions = False
                break
            if finish_reason == FinishReason.TOOL_CALLS:
                chat_history.add_message(message=full_content)
                await self._process_tool_calls(full_content, kernel, chat_history, arguments)
                break

    # endregion
    # region content creation

    def _create_chat_message_content(
        self, response: ChatCompletion, choice: Choice, response_metadata: Dict[str, Any]
    ) -> OpenAIChatMessageContent:
        """Create a chat message content object from a choice."""
        metadata = self._get_metadata_from_chat_choice(choice)
        metadata.update(response_metadata)
        return OpenAIChatMessageContent(
            inner_content=response,
            ai_model_id=self.ai_model_id,
            metadata=metadata,
            role=ChatRole(choice.message.role),
            content=choice.message.content,
            function_call=self._get_function_call_from_chat_choice(choice),
            tool_calls=self._get_tool_calls_from_chat_choice(choice),
        )

    def _create_streaming_chat_message_content(
        self,
        chunk: ChatCompletionChunk,
        choice: ChunkChoice,
        chunk_metadata: Dict[str, Any],
    ):
        """Create a streaming chat message content object from a choice."""
        metadata = self._get_metadata_from_chat_choice(choice)
        metadata.update(chunk_metadata)
        return OpenAIStreamingChatMessageContent(
            choice_index=choice.index,
            inner_content=chunk,
            ai_model_id=self.ai_model_id,
            metadata=metadata,
            role=ChatRole(choice.delta.role) if choice.delta.role else None,
            content=choice.delta.content,
            finish_reason=FinishReason(choice.finish_reason) if choice.finish_reason else None,
            function_call=self._get_function_call_from_chat_choice(choice),
            tool_calls=self._get_tool_calls_from_chat_choice(choice),
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

    def _get_tool_calls_from_chat_choice(self, choice: Union[Choice, ChunkChoice]) -> Optional[List[ToolCall]]:
        """Get tool calls from a chat choice."""
        if isinstance(choice, Choice):
            content = choice.message
        else:
            content = choice.delta
        if content.tool_calls is None:
            return None
        return [
            ToolCall(
                id=tool.id,
                type=tool.type,
                function=FunctionCall(name=tool.function.name, arguments=tool.function.arguments),
            )
            for tool in content.tool_calls
        ]

    def _get_function_call_from_chat_choice(self, choice: Union[Choice, ChunkChoice]) -> Optional[FunctionCall]:
        """Get a function call from a chat choice."""
        if isinstance(choice, Choice):
            content = choice.message
        else:
            content = choice.delta
        if content.function_call is None:
            return None
        return FunctionCall(name=content.function_call.name, arguments=content.function_call.arguments)

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
        result: Union[OpenAIChatMessageContent, OpenAIStreamingChatMessageContent],
        kernel: "Kernel",
        chat_history: ChatHistory,
        arguments: "KernelArguments",
    ) -> None:
        """Processes the tool calls in the result and return it as part of the chat history."""
        logger.info(f"processing {len(result.tool_calls)} tool calls")
        args_cloned = copy(arguments)
        for tool_call in result.tool_calls:
            if tool_call.function is None:
                continue
            try:
                func_args = tool_call.function.parse_arguments()
                args_cloned.update(func_args)
            except FunctionCallInvalidArgumentsException as exc:
                logger.exception(
                    f"Received invalid arguments for function {tool_call.function.name}: {exc}. Trying tool call again."
                )
                msg = OpenAIChatMessageContent(
                    role=ChatRole.TOOL,
                    content="The tool call arguments are malformed, please try again.",
                    tool_call_id=tool_call.id,
                    metadata={"function_name": tool_call.function.name},
                )
                chat_history.add_message(message=msg)
                continue
            logger.info(f"Calling {tool_call.function.name} function with args: {tool_call.function.arguments}")
            try:
                func_result = await kernel.invoke(**tool_call.function.split_name_dict(), arguments=args_cloned)
            except Exception as exc:
                logger.exception(f"Error occurred while invoking function {tool_call.function.name}")
                raise ServiceInvalidResponseError(
                    f"Error occurred while invoking function {tool_call.function.name}"
                ) from exc
            msg = OpenAIChatMessageContent(
                role=ChatRole.TOOL,
                content=str(func_result),
                tool_call_id=tool_call.id,
                metadata={"function_name": tool_call.function.name, "function_arguments": func_result.metadata},
            )
            chat_history.add_message(message=msg)

    def _should_return_completions_response(
        self,
        completions: Union[List[OpenAIChatMessageContent], List[OpenAIStreamingChatMessageContent]],
        tool_call_behavior: ToolCallBehavior,
    ) -> bool:
        """Determines if the completions should be returned."""
        return (
            not tool_call_behavior.auto_invoke_kernel_functions
            or any(not isinstance(completion, OpenAIChatMessageContent) for completion in completions)
            or any(not hasattr(completion, "tool_calls") or not completion.tool_calls for completion in completions)
        )


# endregion
