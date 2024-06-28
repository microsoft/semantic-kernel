# Copyright (c) Microsoft. All rights reserved.
import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from copy import copy
from functools import reduce
from typing import TYPE_CHECKING, Any

from semantic_kernel.connectors.ai.function_call_behavior import (
    EnabledFunctions,
    FunctionCallBehavior,
    FunctionCallConfiguration,
    RequiredFunction,
)
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.exceptions import (
    FunctionCallInvalidArgumentsException,
    ServiceInvalidExecutionSettingsError,
)
from semantic_kernel.filters.auto_function_invocation.auto_function_invocation_context import (
    AutoFunctionInvocationContext,
)
from semantic_kernel.filters.filter_types import FilterTypes
from semantic_kernel.filters.kernel_filters_extension import _rebuild_auto_function_invocation_context
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.services.ai_service_client_base import AIServiceClientBase

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.contents.chat_history import ChatHistory
    from semantic_kernel.contents.chat_message_content import ChatMessageContent
    from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
    from semantic_kernel.filters.auto_function_invocation.auto_function_invocation_context import (
        AutoFunctionInvocationContext,
    )
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)


class ChatCompletionClientBase(AIServiceClientBase, ABC):

    # region abstract methods

    @abstractmethod
    async def get_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
        **kwargs: Any,
    ) -> list["ChatMessageContent"]:
        """Method to convert between connector and semantic kernel objects.
        
        This method is called by the invoke method this method needs to be implemented by the corresponding connector.
        The Goal of the method is to return a list of ChatMessageContent that represent the response from connector
        to automate function calling.

        Args:
            chat_history (ChatHistory): A list of chats in a chat_history object, that can be
                rendered into messages from system, user, assistant and tools.
            settings (PromptExecutionSettings): Settings for the request.
            kwargs (Dict[str, Any]): The optional arguments.

        Returns:
            Union[str, List[str]]: A string or list of strings representing the response(s) from the LLM.
        """
        pass

    @abstractmethod
    def get_streaming_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
        **kwargs: Any,
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
        """Method to convert between connector and semantic kernel objects.
        
        This method is called by the invoke method this method needs to be implemented by the corresponding connector.
        The Goal of the method is to return a list of ChatMessageContent that represent the response from connector
        to automate function calling.

        Args:
            chat_history (ChatHistory): A list of chat chat_history, that can be rendered into a
                set of chat_history, from system, user, assistant and function.
            settings (PromptExecutionSettings): Settings for the request.
            kwargs (Dict[str, Any]): The optional arguments.

        Yields:
            A stream representing the response(s) from the LLM.
        """
        ...

    # endregion
    # region function calling config

    def update_settings_from_function_call_configuration(
        self,
        function_call_configuration: "FunctionCallConfiguration",
        settings: "PromptExecutionSettings",
    ) -> None:
        """This Method is used to convert the function call configuration to the desired format for the connector.
        
        Configure the conversion from kernel function to the desired format for the connector.
        To implement function calling in the connector, this method should be overridden.

        The settings object needs to be updated with the function call configuration.

        Args:
            function_call_configuration (FunctionCallConfiguration): The function call configuration.
            settings (PromptExecutionSettings): The settings to update.
        """
        raise NotImplementedError("Function Calling is not implemented for this Connector.")
    
    # endregion

    def _prepare_chat_history_for_request(
        self,
        chat_history: "ChatHistory",
        role_key: str = "role",
        content_key: str = "content",
    ) -> list[dict[str, str | None]]:
        """Prepare the chat history for a request.

        Allowing customization of the key names for role/author, and optionally overriding the role.

        ChatRole.TOOL messages need to be formatted different than system/user/assistant messages:
            They require a "tool_call_id" and (function) "name" key, and the "metadata" key should
            be removed. The "encoding" key should also be removed.

        Args:
            chat_history (ChatHistory): The chat history to prepare.
            role_key (str): The key name for the role/author.
            content_key (str): The key name for the content/message.

        Returns:
            List[Dict[str, Optional[str]]]: The prepared chat history.
        """
        return [message.to_dict(role_key=role_key, content_key=content_key) for message in chat_history.messages]
    
    # region invoke 
    async def invoke(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
        **kwargs: Any
    ) -> list["ChatMessageContent"]:
        """This method is called by the kernel to perform the chat completion and potentially execute function calls.

        The Method calls the get_chat_message_contents method to get the response from the connector.
        Then it checks the function calling behavior and executes the function calls if needed.

        Args:
            chat_history (ChatHistory): A list of chat chat_history, that can be rendered into a
                set of chat_history, from system, user, assistant and function.
            settings (PromptExecutionSettings): Settings for the request.
            kwargs (Dict[str, Any]): The optional arguments.
        
        Returns:
            List[Dict[str, Optional[str]]]: The prepared chat history.
        """
        function_call_behavior = self._check_for_function_calling(settings, **kwargs)
        if not function_call_behavior:
            return await self.get_chat_message_contents(chat_history, settings, **kwargs)
        
        kernel = kwargs.get("kernel", None)

        settings.function_call_behavior.configure(
            kernel=kernel,
            update_settings_callback=self.update_settings_from_function_call_configuration,
            settings=settings,
        )

        return await self._execute_function_call_behavior(chat_history, settings, **kwargs)

    async def _execute_function_call_behavior(
            self,
            chat_history: "ChatHistory",
            settings: "PromptExecutionSettings",
            **kwargs: Any
    ) -> list["ChatMessageContent"]:
        """Takes Semantic Kernel Objects and performs function calling with the selected behavior.

        Args:
            chat_history (ChatHistory): A list of chat chat_history, that can be rendered into a
                set of chat_history, from system, user, assistant and function.
            settings (PromptExecutionSettings): Settings for the request.
            kwargs (Dict[str, Any]): The optional arguments.
        
        Returns:
            List[Dict[str, Optional[str]]]: The prepared chat history.
        """
        kernel = kwargs.get("kernel", None)
        arguments = kwargs.get("arguments", None)
        # loop for auto-invoke function calls
        for request_index in range(settings.function_call_behavior.max_auto_invoke_attempts):
            completions = await self.get_chat_message_contents(chat_history=chat_history, settings=settings, **kwargs)
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
        else:
            # do a final call, without function calling when the max has been reached.
            settings.function_call_behavior.auto_invoke_kernel_functions = False
            return await self.get_chat_message_contents(
                    chat_history=chat_history,
                    settings=settings,
                    **kwargs
                )
        
    # endregion
    # region invoke_streaming

    async def invoke_streaming(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
        **kwargs: Any
    ) -> AsyncGenerator[list[StreamingChatMessageContent | None], Any]:
        """This method is called by the kernel to perform the chat completion and potentially execute function calls.

        The Method calls the get_chat_message_contents method to get the response from the connector.
        Then it checks the function calling behavior and executes the function calls if needed.

        Args:
            chat_history (ChatHistory): A list of chat chat_history, that can be rendered into a
                set of chat_history, from system, user, assistant and function.
            settings (PromptExecutionSettings): Settings for the request.
            kwargs (Dict[str, Any]): The optional arguments.

        Yields:
            A stream representing the response(s) from the LLM.
        """
        function_call_behavior = self._check_for_function_calling(settings, **kwargs)
        if not function_call_behavior:
            async for messages in self.get_streaming_chat_message_contents(chat_history, settings, **kwargs):
                yield messages
            return
        
        kernel = kwargs.get("kernel", None)
        settings.function_call_behavior.configure(
            kernel=kernel,
            update_settings_callback=self.update_settings_from_function_call_configuration,
            settings=settings,
        )

        async for chunk in self._execute_function_call_behavior_streaming(chat_history, settings, **kwargs):
            yield chunk
        
    async def _execute_function_call_behavior_streaming(
            self,
            chat_history: "ChatHistory",
            settings: "PromptExecutionSettings",
            **kwargs: Any
    ) -> AsyncGenerator[list[StreamingChatMessageContent | None], Any]:
        """Takes Semantic Kernel Objects and performs function calling with the selected behavior.

        Args:
            chat_history (ChatHistory): A list of chat chat_history, that can be rendered into a
                set of chat_history, from system, user, assistant and function.
            settings (PromptExecutionSettings): Settings for the request.
            kwargs (Dict[str, Any]): The optional arguments.

        Yields:
            A stream representing the response(s) from the LLM.
        """
        kernel = kwargs.get("kernel", None)
        arguments = kwargs.get("arguments", None)

        request_attempts = (
            settings.function_call_behavior.max_auto_invoke_attempts 
            if (settings.function_call_behavior and 
                settings.function_call_behavior.auto_invoke_kernel_functions) 
            else 1
        )
        # hold the messages, if there are more than one response, it will not be used, so we flatten
        for request_index in range(request_attempts):
            all_messages: list[StreamingChatMessageContent] = []
            function_call_returned = False
            async for messages in self.get_streaming_chat_message_contents(chat_history, settings, **kwargs):
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

    # endregion
    # region function calling
    
    async def _process_function_call(
        self,
        function_call: FunctionCallContent,
        chat_history: "ChatHistory",
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
            logger.info(
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
            logger.info(msg)
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
        
    def _check_for_function_calling(self, settings: "PromptExecutionSettings", **kwargs: Any) -> bool:
        """Check if function calling is enabled."""
        if not hasattr(settings, 'function_call_behavior'):
            return False
        if settings.function_call_behavior is None:
            return False
        
        kernel = kwargs.get("kernel", None)
        arguments = kwargs.get("arguments", None)
        if settings.function_call_behavior is not None:
            if kernel is None:
                raise ServiceInvalidExecutionSettingsError(
                    "The kernel is required for tool calls."
                )
            if arguments is None and settings.function_call_behavior.auto_invoke_kernel_functions:
                raise ServiceInvalidExecutionSettingsError(
                    "The kernel arguments are required for auto invoking tool calls."
                )
        return True
        
