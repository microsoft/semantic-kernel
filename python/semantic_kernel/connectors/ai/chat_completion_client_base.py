# Copyright (c) Microsoft. All rights reserved.

import asyncio
import copy
import logging
from abc import ABC
from collections.abc import AsyncGenerator, Callable, Mapping
from functools import reduce
from typing import TYPE_CHECKING, Any, ClassVar

from opentelemetry.trace import Span, Tracer, get_tracer, use_span
from pydantic import Field

from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceType
from semantic_kernel.const import AUTO_FUNCTION_INVOCATION_SPAN_NAME
from semantic_kernel.contents.annotation_content import AnnotationContent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.file_reference_content import FileReferenceContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.exceptions.service_exceptions import ServiceInvalidExecutionSettingsError
from semantic_kernel.services.ai_service_client_base import AIServiceClientBase
from semantic_kernel.utils.telemetry.model_diagnostics.gen_ai_attributes import AVAILABLE_FUNCTIONS

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.contents.chat_history import ChatHistory
    from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)
tracer: Tracer = get_tracer(__name__)

# A reply cut off right after the tool name leaves an empty argument string, and a function whose parameters
# are all optional then runs on its defaults. Only that case is refused; whatever the model did write is
# left to the existing parsing.
CUT_OFF_TOOL_CALL_MESSAGE = (
    "The model's reply was cut off at the token limit before this tool call had complete arguments, so it was "
    "not executed. Retry with a smaller request or a larger token budget."
)


def _arguments_never_written(
    finish_reason: "FinishReason | None", function_call: FunctionCallContent, arguments_written: bool | None = None
) -> bool:
    """A cut-off reply that stopped before writing any argument: the tool would run on its defaults.

    `arguments_written` is the streamed evidence, collected before the aggregation turns empty fragments into
    `"{}"`; without it the finished arguments are judged directly. Connectors that hand over the parsed input
    instead of the raw text (Anthropic, Bedrock) report a call cut off before its arguments as an empty
    mapping, while a deliberate no-argument call there ends with `tool_use` rather than `length`.
    """
    if finish_reason != FinishReason.LENGTH:
        return False
    raw = function_call.arguments
    if arguments_written is not None:
        return not arguments_written and not isinstance(raw, Mapping)
    if isinstance(raw, str):
        return not raw.strip()
    return raw is None or (isinstance(raw, Mapping) and not raw)


def _fragment_key(function_call: FunctionCallContent) -> str:
    """Which call a streamed chunk belongs to: the index, because only the first chunk carries the call id."""
    return f"index-{function_call.index}" if function_call.index is not None else (function_call.id or "")


def _note_written_arguments(arguments_written: set[str], message: "StreamingChatMessageContent | None") -> None:
    """Remember the streamed calls that already carried argument text, before the aggregation runs.

    A value that holds only an empty object is not text the model wrote: a connector that hands the parsed
    input over serializes a call cut off before its arguments to `"{}"`, and the aggregation would otherwise
    make that look like a call whose arguments were written.
    """
    for item in message.items if message is not None else ():
        if isinstance(item, FunctionCallContent) and _wrote_argument_text(item.arguments):
            arguments_written.add(_fragment_key(item))


def _wrote_argument_text(arguments: "str | Mapping[str, Any] | None") -> bool:
    """Whether a streamed chunk carried argument text the model did write."""
    if isinstance(arguments, str):
        return arguments.strip() not in ("", "{}")
    return bool(arguments)


def _record_refused_calls(chat_history: "ChatHistory", function_calls: list[FunctionCallContent]) -> None:
    """Record a result per refused call so the model learns why nothing ran, instead of seeing silence."""
    logger.warning(
        "The model's reply was cut off at the token limit; %d tool call(s) with incomplete arguments "
        "were not executed.",
        len(function_calls),
    )
    for function_call in function_calls:
        chat_history.add_message(
            ChatMessageContent(
                role=AuthorRole.TOOL,
                items=[
                    FunctionResultContent(
                        id=function_call.id, name=function_call.name, result=CUT_OFF_TOOL_CALL_MESSAGE
                    )
                ],
            )
        )


class ChatCompletionClientBase(AIServiceClientBase, ABC):
    """Base class for chat completion AI services."""

    # Connectors that support function calling should set this to True
    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = False
    instruction_role: str = Field(default_factory=lambda: "system", description="The role for instructions.")

    # region Internal methods to be implemented by the derived classes

    async def _inner_get_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> list["ChatMessageContent"]:
        """Send a chat request to the AI service.

        Args:
            chat_history (ChatHistory): The chat history to send.
            settings (PromptExecutionSettings): The settings for the request.

        Returns:
            chat_message_contents (list[ChatMessageContent]): The chat message contents representing the response(s).
        """
        raise NotImplementedError("The _inner_get_chat_message_contents method is not implemented.")

    async def _inner_get_streaming_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
        function_invoke_attempt: int = 0,
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
        """Send a streaming chat request to the AI service.

        Args:
            chat_history: The chat history to send.
            settings: The settings for the request.
            function_invoke_attempt: The current attempt count for automatically invoking functions.

        Yields:
            streaming_chat_message_contents: The streaming chat message contents.
        """
        raise NotImplementedError("The _inner_get_streaming_chat_message_contents method is not implemented.")
        # Below is needed for mypy: https://mypy.readthedocs.io/en/stable/more_types.html#asynchronous-iterators
        if False:
            yield

    # endregion

    # region Public methods

    async def get_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
        **kwargs: Any,
    ) -> list["ChatMessageContent"]:
        """Create chat message contents, in the number specified by the settings.

        Args:
            chat_history (ChatHistory): A list of chats in a chat_history object, that can be
                rendered into messages from system, user, assistant and tools.
            settings (PromptExecutionSettings): Settings for the request.
            **kwargs (Any): The optional arguments.

        Returns:
            A list of chat message contents representing the response(s) from the LLM.
        """
        from semantic_kernel.connectors.ai.function_calling_utils import (
            merge_function_results,
        )

        # Create a copy of the settings to avoid modifying the original settings
        settings = copy.deepcopy(settings)
        # Later on, we already use the tools or equivalent settings, we cast here.
        if not isinstance(settings, self.get_prompt_execution_settings_class()):
            settings = self.get_prompt_execution_settings_from_settings(settings)

        if not self.SUPPORTS_FUNCTION_CALLING:
            return await self._inner_get_chat_message_contents(chat_history, settings)

        kernel: "Kernel" = kwargs.get("kernel")  # type: ignore
        if settings.function_choice_behavior is not None:
            if kernel is None:
                raise ServiceInvalidExecutionSettingsError("The kernel is required for function calls.")
            self._verify_function_choice_settings(settings)

        if settings.function_choice_behavior and kernel:
            # Configure the function choice behavior into the settings object
            # that will become part of the request to the AI service
            settings.function_choice_behavior.configure(
                kernel=kernel,
                update_settings_callback=self._update_function_choice_settings_callback(),
                settings=settings,
            )

        if (
            settings.function_choice_behavior is None
            or not settings.function_choice_behavior.auto_invoke_kernel_functions
        ):
            return await self._inner_get_chat_message_contents(chat_history, settings)

        # Auto invoke loop
        with use_span(self._start_auto_function_invocation_activity(kernel, settings), end_on_exit=True) as _:
            for request_index in range(settings.function_choice_behavior.maximum_auto_invoke_attempts):
                completions = await self._inner_get_chat_message_contents(chat_history, settings)
                # Get the function call contents from the chat message. There is only one chat message,
                # which should be checked in the `_verify_function_choice_settings` method.
                function_calls = [item for item in completions[0].items if isinstance(item, FunctionCallContent)]
                if (fc_count := len(function_calls)) == 0:
                    return completions

                # Since we have a function call, add the assistant's tool call message to the history
                chat_history.add_message(message=completions[0])

                if refused := [
                    call for call in function_calls if _arguments_never_written(completions[0].finish_reason, call)
                ]:
                    _record_refused_calls(chat_history, refused)
                    function_calls = [call for call in function_calls if call not in refused]
                if (fc_count := len(function_calls)) == 0:
                    continue

                logger.info(f"processing {fc_count} tool calls in parallel.")

                # This function either updates the chat history with the function call results
                # or returns the context, with terminate set to True in which case the loop will
                # break and the function calls are returned.
                results = await asyncio.gather(
                    *[
                        kernel.invoke_function_call(
                            function_call=function_call,
                            chat_history=chat_history,
                            arguments=kwargs.get("arguments"),
                            execution_settings=settings,
                            function_call_count=fc_count,
                            request_index=request_index,
                            function_behavior=settings.function_choice_behavior,
                        )
                        for function_call in function_calls
                    ],
                )

                if any(result.terminate for result in results if result is not None):
                    return merge_function_results(chat_history.messages[-len(results) :])
            else:
                # Do a final call, without function calling when the max has been reached.
                self._reset_function_choice_settings(settings)
                return await self._inner_get_chat_message_contents(chat_history, settings)

    async def get_chat_message_content(
        self, chat_history: "ChatHistory", settings: "PromptExecutionSettings", **kwargs: Any
    ) -> "ChatMessageContent | None":
        """This is the method that is called from the kernel to get a response from a chat-optimized LLM.

        Args:
            chat_history (ChatHistory): A list of chat chat_history, that can be rendered into a
                set of chat_history, from system, user, assistant and function.
            settings (PromptExecutionSettings): Settings for the request.
            kwargs (Dict[str, Any]): The optional arguments.

        Returns:
            A string representing the response from the LLM.
        """
        results = await self.get_chat_message_contents(chat_history=chat_history, settings=settings, **kwargs)
        if results:
            return results[0]
        # this should not happen, should error out before returning an empty list
        return None  # pragma: no cover

    async def get_streaming_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
        **kwargs: Any,
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
        """Create streaming chat message contents, in the number specified by the settings.

        Args:
            chat_history (ChatHistory): A list of chat chat_history, that can be rendered into a
                set of chat_history, from system, user, assistant and function.
            settings (PromptExecutionSettings): Settings for the request.
            kwargs (Dict[str, Any]): The optional arguments.

        Yields:
            A stream representing the response(s) from the LLM.
        """
        from semantic_kernel.connectors.ai.function_calling_utils import (
            merge_streaming_function_results,
        )

        # Create a copy of the settings to avoid modifying the original settings
        settings = copy.deepcopy(settings)
        # Later on, we already use the tools or equivalent settings, we cast here.
        if not isinstance(settings, self.get_prompt_execution_settings_class()):
            settings = self.get_prompt_execution_settings_from_settings(settings)

        if not self.SUPPORTS_FUNCTION_CALLING:
            async for streaming_chat_message_contents in self._inner_get_streaming_chat_message_contents(
                chat_history, settings
            ):
                yield streaming_chat_message_contents
            return

        kernel: "Kernel" = kwargs.get("kernel")  # type: ignore
        if settings.function_choice_behavior is not None:
            if kernel is None:
                raise ServiceInvalidExecutionSettingsError("The kernel is required for function calls.")
            self._verify_function_choice_settings(settings)

        if settings.function_choice_behavior and kernel:
            # Configure the function choice behavior into the settings object
            # that will become part of the request to the AI service
            settings.function_choice_behavior.configure(
                kernel=kernel,
                update_settings_callback=self._update_function_choice_settings_callback(),
                settings=settings,
            )

        if (
            settings.function_choice_behavior is None
            or not settings.function_choice_behavior.auto_invoke_kernel_functions
        ):
            async for streaming_chat_message_contents in self._inner_get_streaming_chat_message_contents(
                chat_history, settings
            ):
                yield streaming_chat_message_contents
            return

        # Auto invoke loop
        with use_span(self._start_auto_function_invocation_activity(kernel, settings), end_on_exit=True) as _:
            for request_index in range(settings.function_choice_behavior.maximum_auto_invoke_attempts):
                # Hold the messages, if there are more than one response, it will not be used, so we flatten
                all_messages: list["StreamingChatMessageContent"] = []
                arguments_written: set[str] = set()
                async for messages in self._inner_get_streaming_chat_message_contents(
                    chat_history, settings, request_index
                ):
                    for msg in messages:
                        if msg is not None:
                            all_messages.append(msg)
                            _note_written_arguments(arguments_written, msg)
                    yield messages

                if not any(isinstance(item, FunctionCallContent) for msg in all_messages for item in msg.items):
                    return

                # There is one FunctionCallContent response stream in the messages, combining now to create
                # the full completion depending on the prompt, the message may contain both function call
                # content and others
                full_completion: StreamingChatMessageContent = reduce(lambda x, y: x + y, all_messages)
                function_calls = [item for item in full_completion.items if isinstance(item, FunctionCallContent)]
                chat_history.add_message(message=full_completion)

                if refused := [
                    call
                    for call in function_calls
                    if _arguments_never_written(
                        full_completion.finish_reason,
                        call,
                        _fragment_key(call) in arguments_written,
                    )
                ]:
                    _record_refused_calls(chat_history, refused)
                    function_calls = [call for call in function_calls if call not in refused]
                    # The results of refused calls reach the caller like any other tool result
                    refused_messages = merge_streaming_function_results(
                        messages=chat_history.messages[-len(refused) :],
                        ai_model_id=self._get_ai_model_id(settings),  # type: ignore
                        function_invoke_attempt=request_index,
                    )
                    if self._yield_function_result_messages(refused_messages):
                        yield refused_messages
                if (fc_count := len(function_calls)) == 0:
                    continue
                logger.info(f"processing {fc_count} tool calls in parallel.")

                # This function either updates the chat history with the function call results
                # or returns the context, with terminate set to True in which case the loop will
                # break and the function calls are returned.
                results = await asyncio.gather(
                    *[
                        kernel.invoke_function_call(
                            function_call=function_call,
                            chat_history=chat_history,
                            arguments=kwargs.get("arguments"),
                            is_streaming=True,
                            execution_settings=settings,
                            function_call_count=fc_count,
                            request_index=request_index,
                            function_behavior=settings.function_choice_behavior,
                        )
                        for function_call in function_calls
                    ],
                )

                # Merge and yield the function results, regardless of the termination status
                # Include the ai_model_id so we can later add two streaming messages together
                # Some settings may not have an ai_model_id, so we need to check for it
                ai_model_id = self._get_ai_model_id(settings)
                function_result_messages = merge_streaming_function_results(
                    messages=chat_history.messages[-len(results) :],
                    ai_model_id=ai_model_id,  # type: ignore
                    function_invoke_attempt=request_index,
                )
                if self._yield_function_result_messages(function_result_messages):
                    yield function_result_messages

                if any(result.terminate for result in results if result is not None):
                    break

    async def get_streaming_chat_message_content(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
        **kwargs: Any,
    ) -> AsyncGenerator["StreamingChatMessageContent | None", Any]:
        """This is the method that is called from the kernel to get a stream response from a chat-optimized LLM.

        Args:
            chat_history (ChatHistory): A list of chat chat_history, that can be rendered into a
                set of chat_history, from system, user, assistant and function.
            settings (PromptExecutionSettings): Settings for the request.
            kwargs (Dict[str, Any]): The optional arguments.

        Yields:
            A stream representing the response(s) from the LLM.
        """
        async for streaming_chat_message_contents in self.get_streaming_chat_message_contents(
            chat_history, settings, **kwargs
        ):
            if streaming_chat_message_contents:
                yield streaming_chat_message_contents[0]
            else:
                # this should not happen, should error out before returning an empty list
                yield None  # pragma: no cover

    # endregion

    # region internal handlers

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
            message.to_dict(role_key=role_key, content_key=content_key)
            for message in chat_history.messages
            if not isinstance(message, (AnnotationContent, FileReferenceContent))
        ]

    def _verify_function_choice_settings(self, settings: "PromptExecutionSettings") -> None:
        """Additional verification to validate settings for function choice behavior.

        Override this method to add additional verification for the settings.

        Args:
            settings (PromptExecutionSettings): The settings to verify.
        """
        return

    def _update_function_choice_settings_callback(
        self,
    ) -> Callable[["FunctionCallChoiceConfiguration", "PromptExecutionSettings", FunctionChoiceType], None]:
        """Return the callback function to update the settings from a function call configuration.

        Override this method to provide a custom callback function to
        update the settings from a function call configuration.
        """
        return lambda configuration, settings, choice_type: None

    def _reset_function_choice_settings(self, settings: "PromptExecutionSettings") -> None:
        """Reset the settings updated by `_update_function_choice_settings_callback`.

        Override this method to reset the settings updated by `_update_function_choice_settings_callback`.

        Args:
            settings (PromptExecutionSettings): The prompt execution settings to reset.
        """
        return

    def _start_auto_function_invocation_activity(self, kernel: "Kernel", settings: "PromptExecutionSettings") -> Span:
        """Start the auto function invocation activity.

        Args:
            kernel (Kernel): The kernel instance.
            settings (PromptExecutionSettings): The prompt execution settings.
        """
        span = tracer.start_span(AUTO_FUNCTION_INVOCATION_SPAN_NAME)

        if settings.function_choice_behavior is not None:
            available_functions = settings.function_choice_behavior.get_config(kernel).available_functions or []
            span.set_attribute(
                AVAILABLE_FUNCTIONS,
                ",".join([f.fully_qualified_name for f in available_functions]),
            )

        return span

    def _get_ai_model_id(self, settings: "PromptExecutionSettings") -> str:
        """Retrieve the AI model ID from settings if available.

        Attempt to get ai_model_id from the settings object. If it doesn't exist or
        is blank, fallback to self.ai_model_id (from AIServiceClientBase).
        """
        return getattr(settings, "ai_model_id", self.ai_model_id) or self.ai_model_id

    def _yield_function_result_messages(self, function_result_messages: list) -> bool:
        """Determine if the function result messages should be yielded.

        If there are messages and if the first message has items, then yield the messages.
        """
        return len(function_result_messages) > 0 and len(function_result_messages[0].items) > 0

    # endregion
