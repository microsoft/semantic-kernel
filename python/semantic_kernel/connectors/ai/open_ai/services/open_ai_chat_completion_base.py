# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from collections.abc import AsyncGenerator
from copy import copy
from functools import reduce
from typing import TYPE_CHECKING, Any

from openai import AsyncStream
from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.function_call_behavior import (
    EnabledFunctions,
    FunctionCallBehavior,
    RequiredFunction,
)
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import OpenAIHandler
from semantic_kernel.connectors.ai.open_ai.services.utils import update_settings_from_function_call_configuration
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
from semantic_kernel.filters.auto_function_invocation.auto_function_invocation_context import (
    AutoFunctionInvocationContext,
)
from semantic_kernel.filters.filter_types import FilterTypes
from semantic_kernel.filters.kernel_filters_extension import _rebuild_auto_function_invocation_context
from semantic_kernel.functions.function_result import FunctionResult

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)


class InvokeTermination(Exception):
    """Exception for termination of function invocation."""

    pass


class OpenAIChatCompletionBase(OpenAIHandler, ChatCompletionClientBase):
    """OpenAI Chat completion class."""

    # region Overriding base class methods
    # most of the methods are overridden from the ChatCompletionClientBase class, otherwise it is mentioned

    # override from AIServiceClientBase
    def get_prompt_execution_settings_class(self) -> "PromptExecutionSettings":
        """Create a request settings object."""
        return OpenAIChatPromptExecutionSettings

    async def get_chat_message_contents(
        self,
        chat_history: ChatHistory,
        settings: OpenAIChatPromptExecutionSettings,
        **kwargs: Any,
    ) -> list["ChatMessageContent"]:
        """Executes a chat completion request and returns the result.

        Args:
            chat_history (ChatHistory): The chat history to use for the chat completion.
            settings (OpenAIChatPromptExecutionSettings | AzureChatPromptExecutionSettings): The settings to use
                for the chat completion request.
            kwargs (Dict[str, Any]): The optional arguments.

        Returns:
            List[ChatMessageContent]: The completion result(s).
        """
        kernel = kwargs.get("kernel", None)
        arguments = kwargs.get("arguments", None)
        if settings.function_call_behavior is not None:
            if kernel is None:
                raise ServiceInvalidExecutionSettingsError(
                    "The kernel is required for OpenAI tool calls."
                )
            if arguments is None and settings.function_call_behavior.auto_invoke_kernel_functions:
                raise ServiceInvalidExecutionSettingsError(
                    "The kernel arguments are required for auto invoking OpenAI tool calls."
                )
            if settings.number_of_responses is not None and settings.number_of_responses > 1:
                raise ServiceInvalidExecutionSettingsError(
                    "Auto-invocation of tool calls may only be used with a "
                    "OpenAIChatPromptExecutions.number_of_responses of 1."
                )

        # behavior for non-function calling or for enable, but not auto-invoke.
        self._prepare_settings(settings, chat_history, stream_request=False, kernel=kernel)
        if settings.function_call_behavior is None or (
            settings.function_call_behavior and not settings.function_call_behavior.auto_invoke_kernel_functions
        ):
            return await self._send_chat_request(settings)

        # loop for auto-invoke function calls
        for request_index in range(settings.function_call_behavior.max_auto_invoke_attempts):
            completions = await self._send_chat_request(settings)
            # there is only one chat message, this was checked earlier
            chat_history.add_message(message=completions[0])
            # get the function call contents from the chat message
            function_calls = [item for item in chat_history.messages[-1].items if isinstance(item, FunctionCallContent)]
            if (fc_count := len(function_calls)) == 0:
                return completions

            logger.info(f"processing {fc_count} tool calls in parallel.")

            # this function either updates the chat history with the function call results
            # or returns the context, with terminate set to True
            # in which case the loop will break and the function calls are returned.
            results = await asyncio.gather(
                *[
                    self._process_function_call(
                        function_call=function_call,
                        chat_history=chat_history,
                        kernel=kernel,
                        arguments=arguments,
                        function_call_count=fc_count,
                        request_index=request_index,
                        function_call_behavior=settings.function_call_behavior,
                    )
                    for function_call in function_calls
                ],
            )

            if any(result.terminate for result in results if result is not None):
                return completions

            self._update_settings(settings, chat_history, kernel=kernel)
        else:
            # do a final call, without function calling when the max has been reached.
            settings.function_call_behavior.auto_invoke_kernel_functions = False
            return await self._send_chat_request(settings)

    async def get_streaming_chat_message_contents(
        self,
        chat_history: ChatHistory,
        settings: OpenAIChatPromptExecutionSettings,
        **kwargs: Any,
    ) -> AsyncGenerator[list[StreamingChatMessageContent | None], Any]:
        """Executes a streaming chat completion request and returns the result.

        Args:
            chat_history (ChatHistory): The chat history to use for the chat completion.
            settings (OpenAIChatPromptExecutionSettings | AzureChatPromptExecutionSettings): The settings to use
                for the chat completion request.
            kwargs (Dict[str, Any]): The optional arguments.

        Yields:
            List[StreamingChatMessageContent]: A stream of
                StreamingChatMessageContent when using Azure.
        """
        kernel = kwargs.get("kernel", None)
        arguments = kwargs.get("arguments", None)
        if settings.function_call_behavior is not None:
            if kernel is None:
                raise ServiceInvalidExecutionSettingsError(
                    "The kernel is required for OpenAI tool calls."
                )
            if arguments is None and settings.function_call_behavior.auto_invoke_kernel_functions:
                raise ServiceInvalidExecutionSettingsError(
                    "The kernel arguments are required for auto invoking OpenAI tool calls."
                )
            if settings.number_of_responses is not None and settings.number_of_responses > 1:
                raise ServiceInvalidExecutionSettingsError(
                    "Auto-invocation of tool calls may only be used with a "
                    "OpenAIChatPromptExecutions.number_of_responses of 1."
                )

        # Prepare settings for streaming requests
        self._prepare_settings(settings, chat_history, stream_request=True, kernel=kernel)

        request_attempts = (
            settings.function_call_behavior.max_auto_invoke_attempts if settings.function_call_behavior else 1
        )
        # hold the messages, if there are more than one response, it will not be used, so we flatten
        for request_index in range(request_attempts):
            all_messages: list[StreamingChatMessageContent] = []
            function_call_returned = False
            async for messages in self._send_chat_stream_request(settings):
                for msg in messages:
                    if msg is not None:
                        all_messages.append(msg)
                        if any(isinstance(item, FunctionCallContent) for item in msg.items):
                            function_call_returned = True
                yield messages

            if (
                settings.function_call_behavior is None
                or (
                    settings.function_call_behavior and not settings.function_call_behavior.auto_invoke_kernel_functions
                )
                or not function_call_returned
            ):
                # no need to process function calls
                # note that we don't check the FinishReason and instead check whether there are any tool calls,
                # as the service may return a FinishReason of "stop" even if there are tool calls to be made,
                # in particular if a required tool is specified.
                return

            # there is one response stream in the messages, combining now to create the full completion
            # depending on the prompt, the message may contain both function call content and others
            full_completion: StreamingChatMessageContent = reduce(lambda x, y: x + y, all_messages)
            function_calls = [item for item in full_completion.items if isinstance(item, FunctionCallContent)]
            chat_history.add_message(message=full_completion)

            fc_count = len(function_calls)
            logger.info(f"processing {fc_count} tool calls in parallel.")

            # this function either updates the chat history with the function call results
            # or returns the context, with terminate set to True
            # in which case the loop will break and the function calls are returned.
            # Exceptions are not caught, that is up to the developer, can be done with a filter
            results = await asyncio.gather(
                *[
                    self._process_function_call(
                        function_call=function_call,
                        chat_history=chat_history,
                        kernel=kernel,
                        arguments=arguments,
                        function_call_count=fc_count,
                        request_index=request_index,
                        function_call_behavior=settings.function_call_behavior,
                    )
                    for function_call in function_calls
                ],
            )
            if any(result.terminate for result in results if result is not None):
                return

            self._update_settings(settings, chat_history, kernel=kernel)

    def _chat_message_content_to_dict(self, message: "ChatMessageContent") -> dict[str, str | None]:
        msg = super()._chat_message_content_to_dict(message)
        if message.role == AuthorRole.ASSISTANT:
            if tool_calls := getattr(message, "tool_calls", None):
                msg["tool_calls"] = [tool_call.model_dump() for tool_call in tool_calls]
            if function_call := getattr(message, "function_call", None):
                msg["function_call"] = function_call.model_dump_json()
        if message.role == AuthorRole.TOOL:
            if tool_call_id := getattr(message, "tool_call_id", None):
                msg["tool_call_id"] = tool_call_id
            if message.metadata and "function" in message.metadata:
                msg["name"] = message.metadata["function_name"]
        return msg

    # endregion
    # region internal handlers

    async def _send_chat_request(self, settings: OpenAIChatPromptExecutionSettings) -> list["ChatMessageContent"]:
        """Send the chat request."""
        response = await self._send_request(request_settings=settings)
        response_metadata = self._get_metadata_from_chat_response(response)
        return [self._create_chat_message_content(response, choice, response_metadata) for choice in response.choices]

    async def _send_chat_stream_request(
        self, settings: OpenAIChatPromptExecutionSettings
    ) -> AsyncGenerator[list["StreamingChatMessageContent | None"], None]:
        """Send the chat stream request."""
        response = await self._send_request(request_settings=settings)
        if not isinstance(response, AsyncStream):
            raise ServiceInvalidResponseError("Expected an AsyncStream[ChatCompletionChunk] response.")
        async for chunk in response:
            if len(chunk.choices) == 0:
                continue
            chunk_metadata = self._get_metadata_from_streaming_chat_response(chunk)
            yield [
                self._create_streaming_chat_message_content(chunk, choice, chunk_metadata) for choice in chunk.choices
            ]

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
        chunk_metadata: dict[str, Any],
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

    def _get_metadata_from_chat_response(self, response: ChatCompletion) -> dict[str, Any]:
        """Get metadata from a chat response."""
        return {
            "id": response.id,
            "created": response.created,
            "system_fingerprint": response.system_fingerprint,
            "usage": getattr(response, "usage", None),
        }

    def _get_metadata_from_streaming_chat_response(self, response: ChatCompletionChunk) -> dict[str, Any]:
        """Get metadata from a streaming chat response."""
        return {
            "id": response.id,
            "created": response.created,
            "system_fingerprint": response.system_fingerprint,
        }

    def _get_metadata_from_chat_choice(self, choice: Choice | ChunkChoice) -> dict[str, Any]:
        """Get metadata from a chat choice."""
        return {
            "logprobs": getattr(choice, "logprobs", None),
        }

    def _get_tool_calls_from_chat_choice(self, choice: Choice | ChunkChoice) -> list[FunctionCallContent]:
        """Get tool calls from a chat choice."""
        content = choice.message if isinstance(choice, Choice) else choice.delta
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

    def _get_function_call_from_chat_choice(self, choice: Choice | ChunkChoice) -> list[FunctionCallContent]:
        """Get a function call from a chat choice."""
        content = choice.message if isinstance(choice, Choice) else choice.delta
        if content.function_call is None:
            return []
        return [
            FunctionCallContent(
                id="legacy_function_call", name=content.function_call.name, arguments=content.function_call.arguments
            )
        ]

    # endregion
    # region request preparation

    def _prepare_settings(
        self,
        settings: OpenAIChatPromptExecutionSettings,
        chat_history: ChatHistory,
        stream_request: bool = False,
        kernel: "Kernel | None" = None,
    ) -> None:
        """Prepare the prompt execution settings for the chat request."""
        settings.stream = stream_request
        if not settings.ai_model_id:
            settings.ai_model_id = self.ai_model_id
        self._update_settings(settings=settings, chat_history=chat_history, kernel=kernel)

    def _update_settings(
        self,
        settings: OpenAIChatPromptExecutionSettings,
        chat_history: ChatHistory,
        kernel: "Kernel | None" = None,
    ) -> None:
        """Update the settings with the chat history."""
        settings.messages = self._prepare_chat_history_for_request(chat_history)
        if settings.function_call_behavior and kernel:
            settings.function_call_behavior.configure(
                kernel=kernel,
                update_settings_callback=update_settings_from_function_call_configuration,
                settings=settings,
            )

    # endregion
    # region function calling

    async def _process_function_call(
        self,
        function_call: FunctionCallContent,
        chat_history: ChatHistory,
        kernel: "Kernel",
        arguments: "KernelArguments",
        function_call_count: int,
        request_index: int,
        function_call_behavior: FunctionCallBehavior,
    ) -> "AutoFunctionInvocationContext | None":
        """Processes the tool calls in the result and update the chat history."""
        args_cloned = copy(arguments)
        try:
            parsed_args = function_call.parse_arguments()
            if parsed_args:
                args_cloned.update(parsed_args)
        except (FunctionCallInvalidArgumentsException, TypeError) as exc:
            logger.exception(
                f"Received invalid arguments for function {function_call.name}: {exc}. Trying tool call again."
            )
            frc = FunctionResultContent.from_function_call_content_and_result(
                function_call_content=function_call,
                result="The tool call arguments are malformed. Arguments must be in JSON format. Please try again.",
            )
            chat_history.add_message(message=frc.to_chat_message_content())
            return None

        logger.info(f"Calling {function_call.name} function with args: {function_call.arguments}")
        try:
            if function_call.name is None:
                raise ValueError("The function name is required.")
            if (
                isinstance(function_call_behavior, RequiredFunction)
                and function_call.name != function_call_behavior.function_fully_qualified_name
            ):
                raise ValueError(
                    f"Only function: {function_call_behavior.function_fully_qualified_name} "
                    f"is allowed, {function_call.name} is not allowed."
                )
            if isinstance(function_call_behavior, EnabledFunctions):
                enabled_functions = [
                    func.fully_qualified_name
                    for func in kernel.get_list_of_function_metadata(function_call_behavior.filters)
                ]
                if function_call.name not in enabled_functions:
                    raise ValueError(
                        f"Only functions: {enabled_functions} are allowed, {function_call.name} is not allowed."
                    )
            function_to_call = kernel.get_function(function_call.plugin_name, function_call.function_name)
        except Exception as exc:
            logger.exception(f"Could not find function {function_call.name}: {exc}.")
            frc = FunctionResultContent.from_function_call_content_and_result(
                function_call_content=function_call,
                result="The tool call could not be found, please try again and make sure to validate the name.",
            )
            chat_history.add_message(message=frc.to_chat_message_content())
            return None

        num_required_func_params = len([param for param in function_to_call.parameters if param.is_required])
        if len(parsed_args) < num_required_func_params:
            msg = (
                f"There are `{num_required_func_params}` tool call arguments required and "
                f"only `{len(parsed_args)}` received. The required arguments are: "
                f"{[param.name for param in function_to_call.parameters if param.is_required]}. "
                "Please provide the required arguments and try again."
            )
            logger.exception(msg)
            frc = FunctionResultContent.from_function_call_content_and_result(
                function_call_content=function_call,
                result=msg,
            )
            chat_history.add_message(message=frc.to_chat_message_content())
            return None

        _rebuild_auto_function_invocation_context()
        invocation_context = AutoFunctionInvocationContext(
            function=function_to_call,
            kernel=kernel,
            arguments=args_cloned,
            chat_history=chat_history,
            function_result=FunctionResult(function=function_to_call.metadata, value=None),
            function_count=function_call_count,
            request_sequence_index=request_index,
        )
        if function_call.index is not None:
            invocation_context.function_sequence_index = function_call.index

        stack = kernel.construct_call_stack(
            filter_type=FilterTypes.AUTO_FUNCTION_INVOCATION,
            inner_function=self._inner_auto_function_invoke_handler,
        )
        await stack(invocation_context)

        if invocation_context.terminate:
            return invocation_context

        frc = FunctionResultContent.from_function_call_content_and_result(
            function_call_content=function_call, result=invocation_context.function_result
        )
        chat_history.add_message(message=frc.to_chat_message_content())
        return None

    async def _inner_auto_function_invoke_handler(self, context: AutoFunctionInvocationContext):
        """Inner auto function invocation handler."""
        try:
            result = await context.function.invoke(context.kernel, context.arguments)
            if result:
                context.function_result = result
        except Exception as exc:
            logger.exception(f"Error invoking function {context.function.fully_qualified_name}: {exc}.")
            value = f"An error occurred while invoking the function {context.function.fully_qualified_name}: {exc}"
            if context.function_result is not None:
                context.function_result.value = value
            else:
                context.function_result = FunctionResult(function=context.function.metadata, value=value)
            return


# endregion
