# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import AsyncGenerator
from typing import Any

from mistralai.async_client import MistralAsyncClient
from mistralai.models.chat_completion import (
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatCompletionResponseStreamChoice,
    ChatCompletionStreamResponse,
)
from pydantic import ValidationError

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.mistral_ai.prompt_execution_settings.mistral_ai_prompt_execution_settings import (
    MistralAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.mistral_ai.services.mistral_ai_config_base import MistralAIConfigBase
from semantic_kernel.connectors.ai.mistral_ai.services.mistral_ai_handler import MistralAIHandler
from semantic_kernel.connectors.ai.mistral_ai.settings.mistral_ai_settings import MistralAISettings
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.exceptions.service_exceptions import (
    ServiceInitializationError,
    ServiceInvalidExecutionSettingsError,
    ServiceInvalidResponseError,
)
from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)


class MistralAIChatCompletion(MistralAIConfigBase, MistralAIHandler, ChatCompletionClientBase):
    """Mistral Chat completion class."""

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
            async_client (Optional[MistralAsyncClient]): An existing client to use. (Optional)
            env_file_path (str | None): Use the environment settings file as a fallback
                to environment variables. (Optional)
            env_file_encoding (str | None): The encoding of the environment settings file. (Optional)
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
        super().__init__(
            ai_model_id=mistralai_settings.chat_model_id,
            api_key=mistralai_settings.api_key.get_secret_value() if mistralai_settings.api_key else None,
            service_id=service_id,
            async_client=async_client,
        )

    def get_prompt_execution_settings_class(self) -> "PromptExecutionSettings":
        """Create a request settings object."""
        return MistralAIChatPromptExecutionSettings

    async def get_chat_message_contents(
        self,
        chat_history: ChatHistory,
        settings: MistralAIChatPromptExecutionSettings,
        **kwargs: Any,
    ) -> list["ChatMessageContent"]:
        """Executes a chat completion request and returns the result.

        Args:
            chat_history (ChatHistory): The chat history to use for the chat completion.
            settings (MistralAIChatPromptExecutionSettings): The settings to use
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
                    "The kernel is required for MistralAI tool calls."
                )
            if arguments is None and settings.function_call_behavior.auto_invoke_kernel_functions:
                raise ServiceInvalidExecutionSettingsError(
                    "The kernel arguments are required for auto invoking MistralAI tool calls."
                )
            if settings.number_of_responses is not None and settings.number_of_responses > 1:
                raise ServiceInvalidExecutionSettingsError(
                    "Auto-invocation of tool calls may only be used with a "
                    "MistralAIChatPromptExecutions.number_of_responses of 1."
                )

        # behavior for non-function calling or for enable, but not auto-invoke.
        self._prepare_settings(settings, chat_history, kernel=kernel)
        if settings.function_call_behavior is None or (
            settings.function_call_behavior and not settings.function_call_behavior.auto_invoke_kernel_functions
        ):
            return await self._send_chat_request(settings)

        # TODO(Nico Möller): Add Function Calling to Mistral
        raise ServiceInvalidResponseError(
            "Function Calling is not implemented yet for Mistral"
        )
       
    async def get_streaming_chat_message_contents(
        self,
        chat_history: ChatHistory,
        settings: MistralAIChatPromptExecutionSettings,
        **kwargs: Any,
    ) -> AsyncGenerator[list[StreamingChatMessageContent | None], Any]:
        """Executes a streaming chat completion request and returns the result.

        Args:
            chat_history (ChatHistory): The chat history to use for the chat completion.
            settings (MistralAIChatPromptExecutionSettings): The settings to use
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
            settings.function_call_behavior.max_auto_invoke_attempts 
            if (settings.function_call_behavior and 
                settings.function_call_behavior.auto_invoke_kernel_functions) 
            else 1
        )
        # hold the messages, if there are more than one response, it will not be used, so we flatten
        for request_index in range(request_attempts):
            all_messages: list[StreamingChatMessageContent] = []
            function_call_returned = False
            async for messages in self._send_chat_stream_request(settings):
                for msg in messages:
                    if msg is not None:
                        all_messages.append(msg)
                        # TODO(Nico Möller): Add Function Calling 
                        # --> See get_streaming_chat_message_contents in oai connector

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

            # TODO(Nico Möller): Add Function Calling --> See get_streaming_chat_message_contents in oai connector

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

    async def _send_chat_request(self, settings: MistralAIChatPromptExecutionSettings) -> list["ChatMessageContent"]:
        """Send the chat request."""
        response = await self._send_request(request_settings=settings, stream=False)
        response_metadata = self._get_metadata_from_chat_response(response)
        return [self._create_chat_message_content(response, choice, response_metadata) for choice in response.choices]

    async def _send_chat_stream_request(
        self, settings: MistralAIChatPromptExecutionSettings
    ) -> AsyncGenerator[list["StreamingChatMessageContent | None"], None]:
        """Send the chat stream request."""
        response = await self._send_request(request_settings=settings, stream=True)
        if not isinstance(response, AsyncGenerator):
            raise ServiceInvalidResponseError("Expected an AsyncGenerator response.")
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
        self, response: ChatCompletionResponse, choice: ChatCompletionResponseChoice, response_metadata: dict[str, Any]
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
        chunk: ChatCompletionStreamResponse,
        choice: ChatCompletionResponseStreamChoice,
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

    def _get_metadata_from_chat_response(self, response: ChatCompletionResponse) -> dict[str, Any]:
        """Get metadata from a chat response."""
        return {
            "id": response.id,
            "created": response.created,
            "usage": getattr(response, "usage", None),
        }

    def _get_metadata_from_streaming_chat_response(self, response: ChatCompletionStreamResponse) -> dict[str, Any]:
        """Get metadata from a streaming chat response."""
        return {
            "id": response.id,
            "created": response.created,
        }

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

    def _get_function_call_from_chat_choice(
        self,
        choice: ChatCompletionResponseChoice | ChatCompletionResponseStreamChoice
    ) -> list[FunctionCallContent]:
        """Get a function call from a chat choice."""
        content = choice.message if isinstance(choice, ChatCompletionResponseChoice) else choice.delta
        if content.tool_calls is None:
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
        settings: MistralAIChatPromptExecutionSettings,
        chat_history: ChatHistory,
        stream_request: bool = False,
        kernel: "Kernel | None" = None,
    ) -> None:
        """Prepare the prompt execution settings for the chat request."""
        if not settings.ai_model_id:
            settings.ai_model_id = self.ai_model_id
        self._update_settings(settings=settings, chat_history=chat_history, kernel=kernel)

    def _update_settings(
        self,
        settings: MistralAIChatPromptExecutionSettings,
        chat_history: ChatHistory,
        kernel: "Kernel | None" = None,
    ) -> None:
        """Update the settings with the chat history."""
        settings.messages = self._prepare_chat_history_for_request(chat_history)

        # TODO(Nico Möller): Function Calling Mistral Settings --> See _update_settings in oai connector
        
    # endregion
