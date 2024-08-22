# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from collections.abc import AsyncGenerator
from functools import reduce
from typing import Any

from mistralai.async_client import MistralAsyncClient
from mistralai.models.chat_completion import (
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatCompletionResponseStreamChoice,
    ChatCompletionStreamResponse,
    ChatMessage,
    DeltaMessage,
)
from pydantic import ValidationError

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.function_calling_utils import (
    merge_function_results,
    update_settings_from_function_call_configuration,
)
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceType
from semantic_kernel.connectors.ai.mistral_ai.prompt_execution_settings.mistral_ai_prompt_execution_settings import (
    MistralAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.mistral_ai.settings.mistral_ai_settings import MistralAISettings
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents import (
    ChatMessageContent,
    FunctionCallContent,
    StreamingChatMessageContent,
    StreamingTextContent,
    TextContent,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.exceptions.service_exceptions import (
    ServiceInitializationError,
    ServiceInvalidExecutionSettingsError,
    ServiceResponseException,
)
from semantic_kernel.kernel import Kernel
from semantic_kernel.utils.experimental_decorator import experimental_class

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class MistralAIChatCompletion(ChatCompletionClientBase):
    """Mistral Chat completion class."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    async_client: MistralAsyncClient

    def __init__(
        self,
        ai_model_id: str | None = None,
        service_id: str | None = None,
        api_key: str | None = None,
        async_client: MistralAsyncClient | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize an MistralAIChatCompletion service.

        Args:
            ai_model_id (str): MistralAI model name, see
                https://docs.mistral.ai/getting-started/models/
            service_id (str | None): Service ID tied to the execution settings.
            api_key (str | None): The optional API key to use. If provided will override,
                the env vars or .env file value.
            async_client (MistralAsyncClient | None) : An existing client to use. 
            env_file_path (str | None): Use the environment settings file as a fallback
                to environment variables. 
            env_file_encoding (str | None): The encoding of the environment settings file. 
        """
        try:
            mistralai_settings = MistralAISettings.create(
                api_key=api_key,
                chat_model_id=ai_model_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create MistralAI settings.", ex) from ex
        
        if not mistralai_settings.chat_model_id:
            raise ServiceInitializationError("The MistralAI chat model ID is required.")

        if not async_client:
            async_client = MistralAsyncClient(
                api_key=mistralai_settings.api_key.get_secret_value(),
            )

        super().__init__(
            async_client=async_client,
            service_id=service_id or mistralai_settings.chat_model_id,
            ai_model_id=ai_model_id or mistralai_settings.chat_model_id,
        )

    async def get_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
        **kwargs: Any,
    ) -> list["ChatMessageContent"]: 
        """Executes a chat completion request and returns the result.

        Args:
            chat_history (ChatHistory): The chat history to use for the chat completion.
            settings (PromptExecutionSettings): The settings to use
                for the chat completion request.
            kwargs (Dict[str, Any]): The optional arguments.

        Returns:
            List[ChatMessageContent]: The completion result(s).
        """
        if not isinstance(settings, MistralAIChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, MistralAIChatPromptExecutionSettings)  # nosec

        if not settings.ai_model_id:
            settings.ai_model_id = self.ai_model_id
        
        kernel = kwargs.get("kernel", None)
        if settings.function_choice_behavior is not None and kernel is None:
            raise ServiceInvalidExecutionSettingsError("The kernel is required for MistralAI tool calls.")
        assert isinstance(kernel, Kernel)  # nosec
            
        self._update_settings(settings, chat_history, kernel=kernel)

        # behavior for non-function calling or for enable, but not auto-invoke.
        if settings.function_choice_behavior is None or (
            settings.function_choice_behavior and not settings.function_choice_behavior.auto_invoke_kernel_functions
        ):
            return await self._send_chat_request(settings)
        
        # loop for auto-invoke function calls
        for request_index in range(settings.function_choice_behavior.maximum_auto_invoke_attempts):
            completions = await self._send_chat_request(settings)
            # get the function call contents from the chat message, there is only one chat message
            # this was checked earlier
            function_calls = [item for item in completions[0].items if isinstance(item, FunctionCallContent)]
            if (fc_count := len(function_calls)) == 0:
                return completions
            
            # Since we have a function call, add the assistant's tool call message to the history
            chat_history.add_message(message=completions[0])

            logger.info(f"processing {fc_count} tool calls in parallel.")

            # this function either updates the chat history with the function call results
            # or returns the context, with terminate set to True
            # in which case the loop will break and the function calls are returned.
            results = await asyncio.gather(
                *[
                    kernel.invoke_function_call(
                        function_call=function_call,
                        chat_history=chat_history,
                        arguments=kwargs.get("arguments", None),
                        function_call_count=fc_count,
                        request_index=request_index,
                        function_behavior=settings.function_choice_behavior,
                    )
                    for function_call in function_calls
                ],
            )

            if (any(result.terminate for result in results if result is not None)):
                return merge_function_results(chat_history.messages[-len(results) :]) 

            self._update_settings(settings, chat_history, kernel=kernel)
        else:
            # do a final call, without function calling when the max has been reached.
            settings.function_choice_behavior.auto_invoke_kernel_functions = False
            return await self._send_chat_request(settings)
        
    async def _send_chat_request(self,
        settings: "PromptExecutionSettings",
    ) -> list["ChatMessageContent"]:
        
        try:
            response = await self.async_client.chat(**settings.prepare_settings_dict())
        except Exception as ex:
            raise ServiceResponseException(
                f"{type(self)} service failed to complete the prompt",
                ex,
        ) from ex
        
        self.store_usage(response)
        response_metadata = self._get_metadata_from_response(response)
        return [self._create_chat_message_content(response, choice, response_metadata) for choice in response.choices]
        
    async def get_streaming_chat_message_contents(
        self,
        chat_history: ChatHistory,
        settings: PromptExecutionSettings, 
        **kwargs: Any,
    ) -> AsyncGenerator[list[StreamingChatMessageContent], Any]: 
        """Executes a streaming chat completion request and returns the result.

        Args:
            chat_history (ChatHistory): The chat history to use for the chat completion.
            settings (PromptExecutionSettings): The settings to use
                for the chat completion request.
            kwargs (Dict[str, Any]): The optional arguments.

        Yields:
            List[StreamingChatMessageContent]: A stream of
                StreamingChatMessageContent when using Azure.
        """
        if not isinstance(settings, MistralAIChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, MistralAIChatPromptExecutionSettings)  # nosec

        if not settings.ai_model_id:
            settings.ai_model_id = self.ai_model_id

        kernel = kwargs.get("kernel", None)
        if settings.function_choice_behavior is not None and kernel is None:
            raise ServiceInvalidExecutionSettingsError("The kernel is required for MistralAI tool calls.")
        assert isinstance(kernel, Kernel)  # nosec
            
        self._update_settings(settings, chat_history, kernel=kernel)
        
        request_attempts = (
            settings.function_choice_behavior.maximum_auto_invoke_attempts
            if (settings.function_choice_behavior and settings.function_choice_behavior.auto_invoke_kernel_functions)
            else 1
        )
        # hold the messages, if there are more than one response, it will not be used, so we flatten
        for request_index in range(request_attempts):
            all_messages: list[StreamingChatMessageContent] = []
            function_call_returned = False
            async for messages in self._send_chat_request_streaming(settings):
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
                        arguments=kwargs.get("arguments", None),
                        function_call_count=fc_count,
                        request_index=request_index,
                        function_behavior=settings.function_choice_behavior,
                    )
                    for function_call in function_calls
                ],
            )
            if (any(result.terminate for result in results if result is not None)):
                yield merge_function_results(chat_history.messages[-len(results) :])   # type: ignore
                break

            self._update_settings(settings, chat_history, kernel=kernel)

    async def _send_chat_request_streaming(self,
        settings: "PromptExecutionSettings",
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], None]:
        
        try:
            response = self.async_client.chat_stream(**settings.prepare_settings_dict())
        except Exception as ex:
            raise ServiceResponseException(
                f"{type(self)} service failed to complete the prompt",
                ex,
            ) from ex
        async for chunk in response:
            if len(chunk.choices) == 0:
                continue
            chunk_metadata = self._get_metadata_from_response(chunk)
            yield [
                self._create_streaming_chat_message_content(chunk, choice, chunk_metadata) for choice in chunk.choices
            ]
    # region content conversion to SK

    def _create_chat_message_content(
        self, response: ChatCompletionResponse, choice: ChatCompletionResponseChoice, response_metadata: dict[str, Any]
    ) -> "ChatMessageContent":
        """Create a chat message content object from a choice."""
        metadata = self._get_metadata_from_chat_choice(choice)
        metadata.update(response_metadata)

        items: list[Any] = self._get_tool_calls_from_chat_choice(choice)
        
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
        chunk: ChatCompletionStreamResponse,
        choice: ChatCompletionResponseStreamChoice,
        chunk_metadata: dict[str, Any],
    ) -> StreamingChatMessageContent:
        """Create a streaming chat message content object from a choice."""
        metadata = self._get_metadata_from_chat_choice(choice)
        metadata.update(chunk_metadata)

        items: list[Any] = self._get_tool_calls_from_chat_choice(choice)

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

    def _get_metadata_from_response(
            self, 
            response: ChatCompletionResponse | ChatCompletionStreamResponse
    ) -> dict[str, Any]:
        """Get metadata from a chat response."""
        metadata: dict[str, Any] = {
            "id": response.id,
            "created": response.created,
        }
        # Check if usage exists and has a value, then add it to the metadata
        if hasattr(response, "usage") and response.usage is not None:
            metadata["usage"] = response.usage
        
        return metadata

    def _get_metadata_from_chat_choice(
        self,
        choice: ChatCompletionResponseChoice | ChatCompletionResponseStreamChoice
    ) -> dict[str, Any]:
        """Get metadata from a chat choice."""
        return {
            "logprobs": getattr(choice, "logprobs", None),
        }
    
    def _get_tool_calls_from_chat_choice(self,
        choice: ChatCompletionResponseChoice | ChatCompletionResponseStreamChoice
    ) -> list[FunctionCallContent]:
        """Get tool calls from a chat choice."""
        content: ChatMessage | DeltaMessage 
        content = choice.message if isinstance(choice, ChatCompletionResponseChoice) else choice.delta
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
    # endregion

    def get_prompt_execution_settings_class(self) -> "type[MistralAIChatPromptExecutionSettings]":
        """Create a request settings object."""
        return MistralAIChatPromptExecutionSettings
    
    def store_usage(self, response):
        """Store the usage information from the response."""
        if not isinstance(response, AsyncGenerator):
            logger.info(f"MistralAI usage: {response.usage}")
            self.prompt_tokens += response.usage.prompt_tokens
            self.total_tokens += response.usage.total_tokens
            if hasattr(response.usage, "completion_tokens"):
                self.completion_tokens += response.usage.completion_tokens
                
    def _update_settings(
        self,
        settings: MistralAIChatPromptExecutionSettings,
        chat_history: ChatHistory,
        kernel: "Kernel | None" = None,
    ) -> None:
        """Update the settings with the chat history."""
        settings.messages = self._prepare_chat_history_for_request(chat_history)
        if settings.function_choice_behavior and kernel:
            settings.function_choice_behavior.configure(
                kernel=kernel,
                update_settings_callback=update_settings_from_function_call_configuration,
                settings=settings,
            )
            # MistralAI Tool Calls are different from OpenAI Tool Calls
            # tool_choice Required needs to be mapped to any
            if settings.function_choice_behavior.type_ == FunctionChoiceType.REQUIRED:
                settings.tool_choice = "any"
