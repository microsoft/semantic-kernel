# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import AsyncGenerator, Callable
from typing import Any, ClassVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

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
from semantic_kernel.connectors.ai.completion_usage import CompletionUsage
from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
from semantic_kernel.connectors.ai.function_calling_utils import kernel_function_metadata_to_function_call_format
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceType
from semantic_kernel.connectors.ai.mistral_ai.prompt_execution_settings.mistral_ai_prompt_execution_settings import (
    MistralAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.mistral_ai.services.mistral_ai_base import MistralAIBase
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
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError, ServiceResponseException
from semantic_kernel.utils.experimental_decorator import experimental_class
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import (
    trace_chat_completion,
    trace_streaming_chat_completion,
)

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class MistralAIChatCompletion(MistralAIBase, ChatCompletionClientBase):
    """Mistral Chat completion class."""

    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = True

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

    # region Overriding base class methods

    # Override from AIServiceClientBase
    @override
    def get_prompt_execution_settings_class(self) -> "type[MistralAIChatPromptExecutionSettings]":
        """Create a request settings object."""
        return MistralAIChatPromptExecutionSettings

    # Override from AIServiceClientBase
    @override
    def service_url(self) -> str | None:
        if hasattr(self.async_client, "_endpoint"):
            # Best effort to get the endpoint
            return self.async_client._endpoint
        return None

    @override
    @trace_chat_completion(MistralAIBase.MODEL_PROVIDER_NAME)
    async def _inner_get_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> list["ChatMessageContent"]:
        if not isinstance(settings, MistralAIChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, MistralAIChatPromptExecutionSettings)  # nosec

        settings.ai_model_id = settings.ai_model_id or self.ai_model_id
        settings.messages = self._prepare_chat_history_for_request(chat_history)

        try:
            response = await self.async_client.chat(**settings.prepare_settings_dict())
        except Exception as ex:
            raise ServiceResponseException(
                f"{type(self)} service failed to complete the prompt",
                ex,
            ) from ex

        response_metadata = self._get_metadata_from_response(response)
        return [self._create_chat_message_content(response, choice, response_metadata) for choice in response.choices]

    @override
    @trace_streaming_chat_completion(MistralAIBase.MODEL_PROVIDER_NAME)
    async def _inner_get_streaming_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
        if not isinstance(settings, MistralAIChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, MistralAIChatPromptExecutionSettings)  # nosec

        settings.ai_model_id = settings.ai_model_id or self.ai_model_id
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
        self, response: ChatCompletionResponse | ChatCompletionStreamResponse
    ) -> dict[str, Any]:
        """Get metadata from a chat response."""
        metadata: dict[str, Any] = {
            "id": response.id,
            "created": response.created,
        }
        # Check if usage exists and has a value, then add it to the metadata
        if hasattr(response, "usage") and response.usage is not None:
            metadata["usage"] = (
                CompletionUsage(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                ),
            )

        return metadata

    def _get_metadata_from_chat_choice(
        self, choice: ChatCompletionResponseChoice | ChatCompletionResponseStreamChoice
    ) -> dict[str, Any]:
        """Get metadata from a chat choice."""
        return {
            "logprobs": getattr(choice, "logprobs", None),
        }

    def _get_tool_calls_from_chat_choice(
        self, choice: ChatCompletionResponseChoice | ChatCompletionResponseStreamChoice
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

    def update_settings_from_function_call_configuration_mistral(
        self,
        function_choice_configuration: "FunctionCallChoiceConfiguration",
        settings: "PromptExecutionSettings",
        type: "FunctionChoiceType",
    ) -> None:
        """Update the settings from a FunctionChoiceConfiguration."""
        if (
            function_choice_configuration.available_functions
            and hasattr(settings, "tool_choice")
            and hasattr(settings, "tools")
        ):
            settings.tool_choice = type
            settings.tools = [
                kernel_function_metadata_to_function_call_format(f)
                for f in function_choice_configuration.available_functions
            ]
            # Function Choice behavior required maps to MistralAI any
            if (
                settings.function_choice_behavior
                and settings.function_choice_behavior.type_ == FunctionChoiceType.REQUIRED
            ):
                settings.tool_choice = "any"

    @override
    def _update_function_choice_settings_callback(
        self,
    ) -> Callable[[FunctionCallChoiceConfiguration, "PromptExecutionSettings", FunctionChoiceType], None]:
        return self.update_settings_from_function_call_configuration_mistral

    @override
    def _reset_function_choice_settings(self, settings: "PromptExecutionSettings") -> None:
        if hasattr(settings, "tool_choice"):
            settings.tool_choice = None
        if hasattr(settings, "tools"):
            settings.tools = None
