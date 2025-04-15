# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import AsyncGenerator, Callable
from typing import TYPE_CHECKING, Any, ClassVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from mistralai import Mistral
from mistralai.models import (
    AssistantMessage,
    ChatCompletionChoice,
    ChatCompletionResponse,
    CompletionChunk,
    CompletionResponseStreamChoice,
    DeltaMessage,
    ToolCall,
)
from pydantic import ValidationError

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.completion_usage import CompletionUsage
from semantic_kernel.connectors.ai.function_calling_utils import kernel_function_metadata_to_function_call_format
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceType
from semantic_kernel.connectors.ai.mistral_ai.prompt_execution_settings.mistral_ai_prompt_execution_settings import (
    MistralAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.mistral_ai.services.mistral_ai_base import MistralAIBase
from semantic_kernel.connectors.ai.mistral_ai.settings.mistral_ai_settings import MistralAISettings
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
from semantic_kernel.utils.feature_stage_decorator import experimental
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import (
    trace_chat_completion,
    trace_streaming_chat_completion,
)

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class MistralAIChatCompletion(MistralAIBase, ChatCompletionClientBase):
    """Mistral Chat completion class."""

    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = True

    def __init__(
        self,
        ai_model_id: str | None = None,
        service_id: str | None = None,
        api_key: str | None = None,
        async_client: Mistral | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize an MistralAIChatCompletion service.

        Args:
            ai_model_id : MistralAI model name, see
                https://docs.mistral.ai/getting-started/models/
            service_id : Service ID tied to the execution settings.
            api_key : The optional API key to use. If provided will override,
                the env vars or .env file value.
            async_client : An existing client to use.
            env_file_path : Use the environment settings file as a fallback
                to environment variables.
            env_file_encoding : The encoding of the environment settings file.
        """
        try:
            mistralai_settings = MistralAISettings(
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
            async_client = Mistral(
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
            response = await self.async_client.chat.complete_async(**settings.prepare_settings_dict())
        except Exception as ex:
            raise ServiceResponseException(
                f"{type(self)} service failed to complete the prompt",
                ex,
            ) from ex

        if isinstance(response, ChatCompletionResponse):
            response_metadata = self._get_metadata_from_response(response)
            # If there are no choices, return an empty list
            if isinstance(response.choices, list) and len(response.choices) > 0:
                return [
                    self._create_chat_message_content(response, choice, response_metadata)
                    for choice in response.choices
                ]
        return []

    @override
    @trace_streaming_chat_completion(MistralAIBase.MODEL_PROVIDER_NAME)
    async def _inner_get_streaming_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
        function_invoke_attempt: int = 0,
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
        if not isinstance(settings, MistralAIChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, MistralAIChatPromptExecutionSettings)  # nosec

        settings.ai_model_id = settings.ai_model_id or self.ai_model_id
        settings.messages = self._prepare_chat_history_for_request(chat_history)

        try:
            response = await self.async_client.chat.stream_async(**settings.prepare_settings_dict())
        except Exception as ex:
            raise ServiceResponseException(
                f"{type(self)} service failed to complete the prompt",
                ex,
            ) from ex

        # If there is no response end the generator
        if isinstance(response, AsyncGenerator):
            async for chunk in response:
                if len(chunk.data.choices) == 0:
                    continue
                chunk_metadata = self._get_metadata_from_response(chunk.data)
                yield [
                    self._create_streaming_chat_message_content(
                        chunk.data, choice, chunk_metadata, function_invoke_attempt
                    )
                    for choice in chunk.data.choices
                ]

    # endregion

    # region content conversion to SK

    def _create_chat_message_content(
        self, response: ChatCompletionResponse, choice: ChatCompletionChoice, response_metadata: dict[str, Any]
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
        chunk: CompletionChunk,
        choice: CompletionResponseStreamChoice,
        chunk_metadata: dict[str, Any],
        function_invoke_attempt: int,
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
            function_invoke_attempt=function_invoke_attempt,
        )

    def _get_metadata_from_response(self, response: ChatCompletionResponse | CompletionChunk) -> dict[str, Any]:
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
        self, choice: ChatCompletionChoice | CompletionResponseStreamChoice
    ) -> dict[str, Any]:
        """Get metadata from a chat choice."""
        return {
            "logprobs": getattr(choice, "logprobs", None),
        }

    def _get_tool_calls_from_chat_choice(
        self, choice: ChatCompletionChoice | CompletionResponseStreamChoice
    ) -> list[FunctionCallContent]:
        """Get tool calls from a chat choice."""
        content: AssistantMessage | DeltaMessage
        content = choice.message if isinstance(choice, ChatCompletionChoice) else choice.delta
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
            if isinstance(tool, ToolCall)
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
    ) -> Callable[["FunctionCallChoiceConfiguration", "PromptExecutionSettings", FunctionChoiceType], None]:
        return self.update_settings_from_function_call_configuration_mistral

    @override
    def _reset_function_choice_settings(self, settings: "PromptExecutionSettings") -> None:
        if hasattr(settings, "tool_choice"):
            settings.tool_choice = None
        if hasattr(settings, "tools"):
            settings.tools = None
