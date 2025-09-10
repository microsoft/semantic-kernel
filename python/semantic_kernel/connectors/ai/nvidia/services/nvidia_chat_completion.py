# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any, Literal

from openai import AsyncOpenAI
from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import Choice as ChunkChoice
from pydantic import ValidationError

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.completion_usage import CompletionUsage
from semantic_kernel.connectors.ai.nvidia.prompt_execution_settings.nvidia_prompt_execution_settings import (
    NvidiaChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.nvidia.services.nvidia_handler import NvidiaHandler
from semantic_kernel.connectors.ai.nvidia.services.nvidia_model_types import NvidiaModelTypes
from semantic_kernel.connectors.ai.nvidia.settings.nvidia_settings import NvidiaSettings
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents import (
    AuthorRole,
    ChatMessageContent,
    FinishReason,
    FunctionCallContent,
    StreamingChatMessageContent,
    StreamingTextContent,
    TextContent,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError
from semantic_kernel.utils.feature_stage_decorator import experimental
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import (
    trace_chat_completion,
    trace_streaming_chat_completion,
)

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

if TYPE_CHECKING:
    pass

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class NvidiaChatCompletion(NvidiaHandler, ChatCompletionClientBase):
    """NVIDIA Chat completion class.

    This class does not support function calling. The SUPPORTS_FUNCTION_CALLING attribute
    is set to False (inherited from the base class).
    """

    def __init__(
        self,
        ai_model_id: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        service_id: str | None = None,
        client: AsyncOpenAI | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        instruction_role: Literal["system", "user", "assistant", "developer"] | None = None,
    ) -> None:
        """Initialize an NvidiaChatCompletion service.

        Args:
            ai_model_id (str): NVIDIA model name, see
                https://docs.api.nvidia.com/nim/reference/
                If not provided, defaults to "meta/llama-3.1-8b-instruct".
            service_id (str | None): Service ID tied to the execution settings.
            api_key (str | None): The optional API key to use. If provided will override,
                the env vars or .env file value.
            base_url (str | None): Custom API endpoint. (Optional)
            client (Optional[AsyncOpenAI]): An existing client to use. (Optional)
            env_file_path (str | None): Use the environment settings file as a fallback
                to environment variables. (Optional)
            env_file_encoding (str | None): The encoding of the environment settings file. (Optional)
            instruction_role (Literal["system", "user", "assistant", "developer"] | None): The role to use for
                'instruction' messages. Defaults to "system". (Optional)
        """
        try:
            nvidia_settings = NvidiaSettings(
                api_key=api_key,
                base_url=base_url,
                chat_model_id=ai_model_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise ServiceInitializationError("Failed to create NVIDIA settings.", ex) from ex

        if not client and not nvidia_settings.api_key:
            raise ServiceInitializationError("The NVIDIA API key is required.")
        if not nvidia_settings.chat_model_id:
            # Default fallback model: meta/llama-3.1-8b-instruct
            nvidia_settings.chat_model_id = "meta/llama-3.1-8b-instruct"
            logger.warning(f"Default chat model set as: {nvidia_settings.chat_model_id}")

        # Create client if not provided
        if not client:
            client = AsyncOpenAI(
                api_key=nvidia_settings.api_key.get_secret_value() if nvidia_settings.api_key else None,
                base_url=nvidia_settings.base_url,
            )

        super().__init__(
            ai_model_id=nvidia_settings.chat_model_id,
            api_key=nvidia_settings.api_key.get_secret_value() if nvidia_settings.api_key else None,
            base_url=nvidia_settings.base_url,
            service_id=service_id or "",
            ai_model_type=NvidiaModelTypes.CHAT,
            client=client,
            instruction_role=instruction_role or "system",
        )

    @classmethod
    def from_dict(cls: type["NvidiaChatCompletion"], settings: dict[str, Any]) -> "NvidiaChatCompletion":
        """Initialize an NVIDIA service from a dictionary of settings.

        Args:
            settings: A dictionary of settings for the service.
        """
        return cls(
            ai_model_id=settings.get("ai_model_id"),
            api_key=settings.get("api_key"),
            base_url=settings.get("base_url"),
            service_id=settings.get("service_id"),
            env_file_path=settings.get("env_file_path"),
        )

    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        return NvidiaChatPromptExecutionSettings

    @override
    @trace_chat_completion("nvidia")
    async def _inner_get_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> list["ChatMessageContent"]:
        if not isinstance(settings, NvidiaChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, NvidiaChatPromptExecutionSettings)  # nosec

        settings.stream = False
        settings.messages = self._prepare_chat_history_for_request(chat_history)
        settings.ai_model_id = settings.ai_model_id or self.ai_model_id

        # Handle structured output
        self._handle_structured_output(settings)

        response = await self._send_request(settings)
        assert isinstance(response, ChatCompletion)  # nosec
        response_metadata = self._get_metadata_from_chat_response(response)
        return [self._create_chat_message_content(response, choice, response_metadata) for choice in response.choices]

    @override
    @trace_streaming_chat_completion("nvidia")
    async def _inner_get_streaming_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
        function_invoke_attempt: int = 0,
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
        if not isinstance(settings, NvidiaChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, NvidiaChatPromptExecutionSettings)  # nosec

        settings.stream = True
        settings.messages = self._prepare_chat_history_for_request(chat_history)
        settings.ai_model_id = settings.ai_model_id or self.ai_model_id

        # Handle structured output
        self._handle_structured_output(settings)

        response = await self._send_request(settings)
        assert isinstance(response, AsyncGenerator)  # nosec

        async for chunk in response:
            if len(chunk.choices) == 0:
                continue
            chunk_metadata = self._get_metadata_from_chat_response(chunk)
            yield [
                self._create_streaming_chat_message_content(chunk, choice, chunk_metadata, function_invoke_attempt)
                for choice in chunk.choices
            ]

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
            finish_reason=(FinishReason(choice.finish_reason) if choice.finish_reason else None),
        )

    def _create_streaming_chat_message_content(
        self,
        chunk: ChatCompletionChunk,
        choice: ChunkChoice,
        chunk_metadata: dict[str, Any],
        function_invoke_attempt: int,
    ) -> StreamingChatMessageContent:
        """Create a streaming chat message content object from a choice."""
        metadata = self._get_metadata_from_chat_choice(choice)
        metadata.update(chunk_metadata)

        items: list[Any] = self._get_tool_calls_from_chat_choice(choice)
        items.extend(self._get_function_call_from_chat_choice(choice))
        if choice.delta and choice.delta.content is not None:
            items.append(StreamingTextContent(choice_index=choice.index, text=choice.delta.content))
        return StreamingChatMessageContent(
            choice_index=choice.index,
            inner_content=chunk,
            ai_model_id=self.ai_model_id,
            metadata=metadata,
            role=(AuthorRole(choice.delta.role) if choice.delta and choice.delta.role else AuthorRole.ASSISTANT),
            finish_reason=(FinishReason(choice.finish_reason) if choice.finish_reason else None),
            items=items,
            function_invoke_attempt=function_invoke_attempt,
        )

    def _get_metadata_from_chat_response(self, response: ChatCompletion | ChatCompletionChunk) -> dict[str, Any]:
        """Get metadata from a chat response."""
        return {
            "id": response.id,
            "created": response.created,
            "system_fingerprint": getattr(response, "system_fingerprint", None),
            "usage": CompletionUsage.from_openai(response.usage) if response.usage is not None else None,
        }

    def _get_metadata_from_chat_choice(self, choice: Choice | ChunkChoice) -> dict[str, Any]:
        """Get metadata from a chat choice."""
        return {
            "logprobs": getattr(choice, "logprobs", None),
        }

    def _get_tool_calls_from_chat_choice(self, choice: Choice | ChunkChoice) -> list[FunctionCallContent]:
        """Get tool calls from a chat choice."""
        content = choice.message if isinstance(choice, Choice) else choice.delta
        if content and (tool_calls := getattr(content, "tool_calls", None)) is not None:
            return [
                FunctionCallContent(
                    id=tool.id,
                    index=getattr(tool, "index", None),
                    name=tool.function.name,
                    arguments=tool.function.arguments,
                )
                for tool in tool_calls
            ]
        return []

    def _get_function_call_from_chat_choice(self, choice: Choice | ChunkChoice) -> list[FunctionCallContent]:
        """Get function calls from a chat choice."""
        content = choice.message if isinstance(choice, Choice) else choice.delta
        if content and (function_call := getattr(content, "function_call", None)) is not None:
            return [
                FunctionCallContent(
                    id="",
                    name=function_call.name,
                    arguments=function_call.arguments,
                )
            ]
        return []

    def _handle_structured_output(self, request_settings: NvidiaChatPromptExecutionSettings) -> None:
        """Handle structured output for NVIDIA models using nvext parameter."""
        response_format = getattr(request_settings, "response_format", None)
        if response_format:
            # Convert Pydantic model to JSON schema for NVIDIA's guided_json
            if hasattr(response_format, "model_json_schema"):
                # It's a Pydantic model
                schema = response_format.model_json_schema()
                if not request_settings.extra_body:
                    request_settings.extra_body = {}
                request_settings.extra_body["nvext"] = {"guided_json": schema}
            elif isinstance(response_format, dict):
                # It's already a dict, use it directly
                if not request_settings.extra_body:
                    request_settings.extra_body = {}
                request_settings.extra_body["nvext"] = {"guided_json": response_format}

    def _prepare_chat_history_for_request(
        self,
        chat_history: ChatHistory,
        role_key: str = "role",
        content_key: str = "content",
    ) -> list[dict[str, str]]:
        """Prepare chat history for request."""
        messages = []
        for message in chat_history.messages:
            message_dict = {role_key: message.role.value, content_key: message.content}
            messages.append(message_dict)
        return messages
