# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterable,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    Union,
)

from openai import AsyncStream
from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice

from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
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
from semantic_kernel.exceptions import ServiceInvalidExecutionSettingsError, ServiceInvalidResponseError
from semantic_kernel.utils.chat import store_results

if TYPE_CHECKING:
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)


class OpenAIChatCompletionBase(OpenAIHandler, ChatCompletionClientBase):
    """OpenAI Chat completion class."""

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
        **kwargs: Dict[str, Any],
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
        auto_invoke_kernel_functions, max_auto_invoke_attempts = self._get_auto_invoke_execution_settings(settings)
        kernel = self._validate_kernel_for_tool_calling(**kwargs)

        for _ in range(max_auto_invoke_attempts):
            settings = self._prepare_settings(settings, chat_history, stream_request=False)
            completions = await self._send_chat_request(settings)
            if self._should_return_completions_response(completions, auto_invoke_kernel_functions):
                return completions
            await self._process_chat_response_with_tool_call(completions, chat_history, kernel)

    async def complete_chat_stream(
        self,
        chat_history: ChatHistory,
        settings: OpenAIPromptExecutionSettings,
        **kwargs: Dict[str, Any],
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
        auto_invoke_kernel_functions, max_auto_invoke_attempts = self._get_auto_invoke_execution_settings(settings)
        kernel = self._validate_kernel_for_tool_calling(**kwargs)
        tool_call_behavior = None
        if auto_invoke_kernel_functions:
            # Only configure the tool_call_behavior if auto_invoking_functions is true
            tool_call_behavior = ToolCallBehavior(auto_invoke_kernel_functions=auto_invoke_kernel_functions)

        attempts = 0
        continue_loop = True

        while attempts < max_auto_invoke_attempts and continue_loop:
            settings = self._prepare_settings(settings, chat_history, stream_request=True)
            response = await self._send_chat_stream_request(settings)
            async for content in self._process_chat_stream_response(response, tool_call_behavior, chat_history, kernel):
                yield content
                if tool_call_behavior and not tool_call_behavior.auto_invoke_kernel_functions:
                    continue_loop = False
                    break
            attempts += 1

    def _validate_kernel_for_tool_calling(self, **kwargs: Dict[str, Any]) -> "Kernel":
        """Validate that the arguments contains the kernel, which is used for function calling, if applicable."""
        kernel = kwargs.pop("kernel", None)
        if kernel is None:
            raise ServiceInvalidExecutionSettingsError("The kernel argument is required for OpenAI tool calling.")
        return kernel

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
    ) -> None:
        """Process the completions in the chat response"""
        for result in completions:
            # An assistant message needs to be followed be a tool call response
            chat_history = store_results(chat_history=chat_history, results=[result])
            await self._process_tool_calls(result, kernel, chat_history)

    async def _process_chat_stream_response(
        self, response: AsyncStream, tool_call_behavior: ToolCallBehavior, chat_history: ChatHistory, kernel: "Kernel"
    ) -> AsyncIterable[List[OpenAIStreamingChatMessageContent]]:
        """Process the chat stream response and handle tool calls if applicable."""
        stream_chunks, update_storage = {}, self._get_update_storage_fields()
        async for chunk in response:
            if len(chunk.choices) == 0:
                continue

            chunk_metadata = self._get_metadata_from_streaming_chat_response(chunk)
            contents = [
                self._create_streaming_chat_message_content(chunk, choice, chunk_metadata) for choice in chunk.choices
            ]
            self._update_storages(contents, update_storage)

            finish_reason = getattr(contents[0], "finish_reason", None)
            if tool_call_behavior and tool_call_behavior.auto_invoke_kernel_functions and contents[0].tool_calls:
                stream_chunks.setdefault(contents[0].choice_index, []).append(contents[0])
                if finish_reason == FinishReason.STOP:
                    break
            elif (tool_call_behavior and not tool_call_behavior.auto_invoke_kernel_functions) or finish_reason not in (
                FinishReason.STOP,
                FinishReason.TOOL_CALLS,
            ):
                yield contents

            if finish_reason == FinishReason.STOP:
                if tool_call_behavior:
                    tool_call_behavior.auto_invoke_kernel_functions = False
                break

            if stream_chunks and finish_reason == FinishReason.TOOL_CALLS:
                chat_contents = self._build_streaming_message_with_tool_call(stream_chunks, update_storage)
                for chat_content in chat_contents:
                    chat_history = store_results(chat_history=chat_history, results=[chat_content])
                    await self._process_tool_calls(chat_content, kernel, chat_history)
                break

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

    def _get_update_storage_fields(self) -> Dict[str, Dict[int, Any]]:
        """Get the fields to use for storing updates to the messages, tool_calls and function_calls."""
        out_messages = {}
        tool_call_ids_by_index = {}
        function_call_by_index = {}
        return {
            "out_messages": out_messages,
            "tool_call_ids_by_index": tool_call_ids_by_index,
            "function_call_by_index": function_call_by_index,
        }

    def _update_storages(
        self, contents: List[OpenAIStreamingChatMessageContent], update_storage: Dict[str, Dict[int, Any]]
    ):
        """Handle updates to the messages, tool_calls and function_calls.

        This will be used for auto-invoking tools.
        """
        out_messages = update_storage["out_messages"]
        tool_call_ids_by_index = update_storage["tool_call_ids_by_index"]
        function_call_by_index = update_storage["function_call_by_index"]

        for index, content in enumerate(contents):
            if content.content is not None:
                if index not in out_messages:
                    out_messages[index] = str(content)
                else:
                    out_messages[index] += str(content)
            if content.tool_calls is not None:
                for tc in content.tool_calls:
                    if tc.index not in tool_call_ids_by_index:
                        tool_call_ids_by_index[tc.index] = tc
                    else:
                        for tc in content.tool_calls:
                            tool_call_ids_by_index[tc.index] += tc
            if content.function_call is not None:
                for fc in content.function_call:
                    if fc.index not in function_call_by_index:
                        function_call_by_index[fc.index] = fc
                    else:
                        for tc in content.function_call:
                            function_call_by_index[fc.index] += fc

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
                index=getattr(tool, "index", None),
                id=tool.id,
                type=tool.type,
                function=FunctionCall(name=tool.function.name, arguments=tool.function.arguments, id=tool.id),
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

    def _build_streaming_message_with_tool_call(
        self,
        stream_chunks: Dict[int, List[OpenAIStreamingChatMessageContent]],
        update_storage: Dict[str, Dict[int, Any]],
    ) -> List[OpenAIStreamingChatMessageContent]:
        """Build the streaming message with the tool call(s)."""
        if not stream_chunks:
            raise ServiceInvalidResponseError("Expected a non-empty stream_chunks.")
        streaming_chat_message_contents = []
        for _, chunk in stream_chunks.items():
            chat_message: OpenAIStreamingChatMessageContent = None
            for result in chunk:
                chat_message = result if chat_message is None else chat_message + result
            tool_calls_dict = update_storage["tool_call_ids_by_index"]
            chat_message.tool_calls = list(tool_calls_dict.values())
            chat_message.role = ChatRole.ASSISTANT
            streaming_chat_message_contents.append(chat_message)
        return streaming_chat_message_contents

    def _get_auto_invoke_execution_settings(
        self, execution_settings: OpenAIPromptExecutionSettings
    ) -> Tuple[bool, int]:
        """Gets the auto invoke and max iterations settings."""
        if isinstance(execution_settings, OpenAIChatPromptExecutionSettings):
            auto_invoke_kernel_functions = execution_settings.auto_invoke_kernel_functions
            max_auto_invoke_attempts = (
                execution_settings.max_auto_invoke_attempts if auto_invoke_kernel_functions else 1
            )
        else:
            auto_invoke_kernel_functions = False
            max_auto_invoke_attempts = 1

        return auto_invoke_kernel_functions, max_auto_invoke_attempts

    async def _process_tool_calls(
        self,
        result: Union[OpenAIChatMessageContent, OpenAIStreamingChatMessageContent],
        kernel: "Kernel",
        chat_history: ChatHistory,
    ) -> None:
        """Processes the tool calls in the result and return it as part of the chat history."""
        logger.info(f"processing {len(result.tool_calls)} tool calls")
        for tool_call in result.tool_calls:
            func = kernel.func(**tool_call.function.split_name_dict())
            arguments = tool_call.function.to_kernel_arguments()
            logger.info(f"Calling {tool_call.function.name} function with args: {arguments}")
            func_result = await kernel.invoke(func, arguments)
            chat_history.add_tool_message(
                str(func_result.value),
                metadata={"tool_call_id": tool_call.id, "function_name": tool_call.function.name},
            )

    def _should_return_completions_response(
        self,
        completions: Union[List[OpenAIChatMessageContent], List[OpenAIStreamingChatMessageContent]],
        auto_invoke_kernel_functions: bool,
    ) -> bool:
        """Determines if the completions should be returned."""
        return (
            not auto_invoke_kernel_functions
            or any(not isinstance(completion, OpenAIChatMessageContent) for completion in completions)
            or any(not hasattr(completion, "tool_calls") or not completion.tool_calls for completion in completions)
        )
