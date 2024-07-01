# Copyright (c) Microsoft. All rights reserved.
import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from functools import reduce
from typing import TYPE_CHECKING, Any

from semantic_kernel.connectors.ai.function_call_behavior import (
    FunctionCallConfiguration,
)
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.exceptions import (
    ServiceInvalidExecutionSettingsError,
)
from semantic_kernel.services.ai_service_client_base import AIServiceClientBase

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
    from semantic_kernel.contents.chat_history import ChatHistory
    from semantic_kernel.contents.chat_message_content import ChatMessageContent
    from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
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
        type: str,
    ) -> None:
        """This Method is used to convert the function call configuration to the desired format for the connector.
        
        Configure the conversion from kernel function to the desired format for the connector.
        To implement function calling in the connector, this method should be overridden.

        The settings object needs to be updated with the function call configuration.

        Args:
            function_call_configuration (FunctionCallConfiguration): The function call configuration.
            settings (PromptExecutionSettings): The settings to update.
            type (str): The type of the function choice configuration.
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
        function_call_behavior = self._check_for_function_calling_behavior(settings, **kwargs)
        if not function_call_behavior:
            return await self.get_chat_message_contents(chat_history, settings, **kwargs)
        
        kernel = kwargs.get("kernel", None)

        settings.function_choice_behavior.configure(
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
        kernel: Kernel = kwargs.get("kernel", None)
        arguments = kwargs.get("arguments", None)
        # loop for auto-invoke function calls
        for request_index in range(settings.function_choice_behavior.maximum_auto_invoke_attempts):
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
                    kernel.invoke_function_call(
                        function_call=function_call,
                        chat_history=chat_history,
                        arguments=arguments,
                        function_call_count=fc_count,
                        request_index=request_index,
                        function_behavior=settings.function_choice_behavior,
                    )
                    for function_call in function_calls
                ],
            )

            if any(result.terminate for result in results if result is not None):
                return completions
        else:
            # do a final call, without function calling when the max has been reached.
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
        function_call_behavior = self._check_for_function_calling_behavior(settings, **kwargs)
        if not function_call_behavior:
            async for messages in self.get_streaming_chat_message_contents(chat_history, settings, **kwargs):
                yield messages
            return
        
        kernel = kwargs.get("kernel", None)
        settings.function_choice_behavior.configure(
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
        kernel: Kernel = kwargs.get("kernel", None)
        arguments = kwargs.get("arguments", None)

        request_attempts = (
            settings.function_choice_behavior.maximum_auto_invoke_attempts
            if (settings.function_choice_behavior and settings.function_choice_behavior.auto_invoke_kernel_functions)
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
                settings.function_choice_behavior is None
                or (
                    settings.function_choice_behavior
                    and not settings.function_choice_behavior.auto_invoke_kernel_functions
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
                    kernel.invoke_function_call(
                        function_call=function_call,
                        chat_history=chat_history,
                        arguments=arguments,
                        function_call_count=fc_count,
                        request_index=request_index,
                        function_behavior=settings.function_choice_behavior,
                    )
                    for function_call in function_calls
                ],
            )
            if any(result.terminate for result in results if result is not None):
                return

    # endregion
        
    def _check_for_function_calling_behavior(self, settings: "PromptExecutionSettings", **kwargs: Any) -> bool:
        """Check if function calling is enabled."""
        if settings.function_choice_behavior is None:
            return False
        
        kernel = kwargs.get("kernel", None)
        arguments = kwargs.get("arguments", None)
        if settings.function_choice_behavior is not None:
            if kernel is None:
                raise ServiceInvalidExecutionSettingsError(
                    "The kernel is required for tool calls."
                )
            if arguments is None and settings.function_choice_behavior.auto_invoke_kernel_functions:
                raise ServiceInvalidExecutionSettingsError(
                    "The kernel arguments are required for auto invoking tool calls."
                )
        return True
        
