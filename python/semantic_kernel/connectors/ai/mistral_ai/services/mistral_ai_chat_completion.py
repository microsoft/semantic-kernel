# Copyright (c) Microsoft. All rights reserved.

import asyncio
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
from semantic_kernel.connectors.ai.function_call_behavior import (
    FunctionCallConfiguration,
)
from semantic_kernel.connectors.ai.mistral_ai.prompt_execution_settings.mistral_ai_prompt_execution_settings import (
    MistralAIChatPromptExecutionSettings,
)
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
    ServiceResponseException,
)
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata

logger: logging.Logger = logging.getLogger(__name__)


class MistralAIChatCompletion(ChatCompletionClientBase):
    """Mistral Chat completion class."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    async_client: MistralAsyncClient | None = None
    requests_per_second: int = 1

    def __init__(
        self,
        ai_model_id: str | None = None,
        service_id: str | None = None,
        api_key: str | None = None,
        requests_per_second: int | None = None,
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
            requests_per_second (int | None): The number of requests per second to make,
                Free Tier is limited to 1 Request per second.
            async_client (Optional[MistralAsyncClient]): An existing client to use. (Optional)
            env_file_path (str | None): Use the environment settings file as a fallback
                to environment variables. (Optional)
            env_file_encoding (str | None): The encoding of the environment settings file. (Optional)
        """
        try:
            mistralai_settings = MistralAISettings.create(
                api_key=api_key,
                chat_model_id=ai_model_id,
                requests_per_second=requests_per_second,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create MistralAI settings.", ex) from ex
        
        if not async_client:
            async_client = MistralAsyncClient(
                api_key=mistralai_settings.api_key.get_secret_value(),
            )

        super().__init__(
            async_client=async_client,
            requests_per_second=requests_per_second or mistralai_settings.requests_per_second,
            service_id=service_id or mistralai_settings.chat_model_id,
            ai_model_id=ai_model_id or mistralai_settings.chat_model_id,
        )

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
        if not settings.ai_model_id:
            settings.ai_model_id = self.ai_model_id

        settings.messages = self._prepare_chat_history_for_request(chat_history)
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
        if not settings.ai_model_id:
            settings.ai_model_id = self.ai_model_id

        settings.messages = self._prepare_chat_history_for_request(chat_history)
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
        await asyncio.sleep(1 / self.requests_per_second)

    # endregion
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
    ) -> StreamingChatMessageContent | None:
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
        metadata = {
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

    # region function calling config

    def update_settings_from_function_call_configuration(
        self,
        function_call_configuration: FunctionCallConfiguration,
        settings: MistralAIChatPromptExecutionSettings,
    ) -> None:
        """Update the settings from a FunctionCallConfiguration."""
        if function_call_configuration.required_functions:
            raise NotImplementedError("Required functions are not supported.")
        if function_call_configuration.available_functions:
            settings.tool_choice = (
                "auto" if len(function_call_configuration.available_functions) > 0 else None
            )
            settings.tools = [
                self.kernel_function_metadata_to_mistral_tool_format(f)
                for f in function_call_configuration.available_functions
            ]

    def kernel_function_metadata_to_mistral_tool_format(
        self,
        metadata: KernelFunctionMetadata,
    ) -> dict[str, Any]:
        """Convert the kernel function metadata to MistralAI format."""
        return {
            "type": "function",
            "function": {
                "name": metadata.fully_qualified_name,
                "description": metadata.description or "",
                "parameters": {
                    "type": "object",
                    "properties": {
                        param.name: param.schema_data for param in metadata.parameters
                    },
                    "required": [p.name for p in metadata.parameters if p.is_required],
                },
            },
        }
    # endregion

    def get_prompt_execution_settings_class(self) -> "PromptExecutionSettings":
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
