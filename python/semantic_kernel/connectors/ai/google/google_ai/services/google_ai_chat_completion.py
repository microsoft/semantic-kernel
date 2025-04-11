# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from collections.abc import AsyncGenerator, Callable
from typing import TYPE_CHECKING, Any, ClassVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

import google.generativeai as genai
from google.generativeai import GenerativeModel
from google.generativeai.protos import Candidate, Content
from google.generativeai.types import AsyncGenerateContentResponse, GenerateContentResponse, GenerationConfig
from pydantic import ValidationError

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.completion_usage import CompletionUsage
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceType
from semantic_kernel.connectors.ai.google.google_ai.google_ai_prompt_execution_settings import (
    GoogleAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.google.google_ai.google_ai_settings import GoogleAISettings
from semantic_kernel.connectors.ai.google.google_ai.services.google_ai_base import GoogleAIBase
from semantic_kernel.connectors.ai.google.google_ai.services.utils import (
    finish_reason_from_google_ai_to_semantic_kernel,
    format_assistant_message,
    format_tool_message,
    format_user_message,
    update_settings_from_function_choice_configuration,
)
from semantic_kernel.connectors.ai.google.shared_utils import (
    collapse_function_call_results_in_chat_history,
    filter_system_message,
    format_gemini_function_name_to_kernel_function_fully_qualified_name,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import CMC_ITEM_TYPES, ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.streaming_chat_message_content import STREAMING_CMC_ITEM_TYPES as STREAMING_ITEM_TYPES
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.exceptions.service_exceptions import (
    ServiceInitializationError,
    ServiceInvalidExecutionSettingsError,
)
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import (
    trace_chat_completion,
    trace_streaming_chat_completion,
)

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings

logger: logging.Logger = logging.getLogger(__name__)


class GoogleAIChatCompletion(GoogleAIBase, ChatCompletionClientBase):
    """Google AI Chat Completion Client."""

    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = True

    def __init__(
        self,
        gemini_model_id: str | None = None,
        api_key: str | None = None,
        service_id: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize the Google AI Chat Completion Client.

        If no arguments are provided, the service will attempt to load the settings from the environment.
        The following environment variables are used:
        - GOOGLE_AI_GEMINI_MODEL_ID
        - GOOGLE_AI_API_KEY

        Args:
            gemini_model_id (str | None): The Gemini model ID. (Optional)
            api_key (str | None): The API key. (Optional)
            service_id (str | None): The service ID. (Optional)
            env_file_path (str | None): The path to the .env file. (Optional)
            env_file_encoding (str | None): The encoding of the .env file. (Optional)

        Raises:
            ServiceInitializationError: If an error occurs during initialization.
        """
        try:
            google_ai_settings = GoogleAISettings(
                gemini_model_id=gemini_model_id,
                api_key=api_key,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as e:
            raise ServiceInitializationError(f"Failed to validate Google AI settings: {e}") from e
        if not google_ai_settings.gemini_model_id:
            raise ServiceInitializationError("The Google AI Gemini model ID is required.")

        super().__init__(
            ai_model_id=google_ai_settings.gemini_model_id,
            service_id=service_id or google_ai_settings.gemini_model_id,
            service_settings=google_ai_settings,
        )

    # region Overriding base class methods

    # Override from AIServiceClientBase
    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        return GoogleAIChatPromptExecutionSettings

    @override
    @trace_chat_completion(GoogleAIBase.MODEL_PROVIDER_NAME)
    async def _inner_get_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> list["ChatMessageContent"]:
        if not isinstance(settings, GoogleAIChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, GoogleAIChatPromptExecutionSettings)  # nosec

        genai.configure(api_key=self.service_settings.api_key.get_secret_value())
        if not self.service_settings.gemini_model_id:
            raise ServiceInitializationError("The Google AI Gemini model ID is required.")
        model = GenerativeModel(
            model_name=self.service_settings.gemini_model_id,
            system_instruction=filter_system_message(chat_history),
        )

        collapse_function_call_results_in_chat_history(chat_history)

        response: AsyncGenerateContentResponse = await model.generate_content_async(
            contents=self._prepare_chat_history_for_request(chat_history),
            generation_config=GenerationConfig(**settings.prepare_settings_dict()),
            tools=settings.tools,
            tool_config=settings.tool_config,  # type: ignore
        )

        return [self._create_chat_message_content(response, candidate) for candidate in response.candidates]

    @override
    @trace_streaming_chat_completion(GoogleAIBase.MODEL_PROVIDER_NAME)
    async def _inner_get_streaming_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
        function_invoke_attempt: int = 0,
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
        if not isinstance(settings, GoogleAIChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, GoogleAIChatPromptExecutionSettings)  # nosec

        genai.configure(api_key=self.service_settings.api_key.get_secret_value())
        if not self.service_settings.gemini_model_id:
            raise ServiceInitializationError("The Google AI Gemini model ID is required.")
        model = GenerativeModel(
            model_name=self.service_settings.gemini_model_id,
            system_instruction=filter_system_message(chat_history),
        )

        collapse_function_call_results_in_chat_history(chat_history)

        response: AsyncGenerateContentResponse = await model.generate_content_async(
            contents=self._prepare_chat_history_for_request(chat_history),
            generation_config=GenerationConfig(**settings.prepare_settings_dict()),
            tools=settings.tools,
            tool_config=settings.tool_config,  # type: ignore
            stream=True,
        )

        async for chunk in response:
            yield [
                self._create_streaming_chat_message_content(chunk, candidate, function_invoke_attempt)
                for candidate in chunk.candidates
            ]

    @override
    def _verify_function_choice_settings(self, settings: "PromptExecutionSettings") -> None:
        if not isinstance(settings, GoogleAIChatPromptExecutionSettings):
            raise ServiceInvalidExecutionSettingsError("The settings must be an GoogleAIChatPromptExecutionSettings.")
        if settings.candidate_count is not None and settings.candidate_count > 1:
            raise ServiceInvalidExecutionSettingsError(
                "Auto-invocation of tool calls may only be used with a "
                "GoogleAIChatPromptExecutionSettings.candidate_count of 1."
            )

    @override
    def _update_function_choice_settings_callback(
        self,
    ) -> Callable[["FunctionCallChoiceConfiguration", "PromptExecutionSettings", FunctionChoiceType], None]:
        return update_settings_from_function_choice_configuration

    @override
    def _reset_function_choice_settings(self, settings: "PromptExecutionSettings") -> None:
        if hasattr(settings, "tool_config"):
            settings.tool_config = None
        if hasattr(settings, "tools"):
            settings.tools = None

    @override
    def _prepare_chat_history_for_request(
        self,
        chat_history: ChatHistory,
        role_key: str = "role",
        content_key: str = "content",
    ) -> list[Content]:
        chat_request_messages: list[Content] = []

        for message in chat_history.messages:
            if message.role == AuthorRole.SYSTEM:
                # Skip system messages since they are not part of the chat request.
                # System message will be provided as system_instruction in the model.
                continue
            if message.role == AuthorRole.USER:
                chat_request_messages.append(Content(role="user", parts=format_user_message(message)))
            elif message.role == AuthorRole.ASSISTANT:
                chat_request_messages.append(Content(role="model", parts=format_assistant_message(message)))
            elif message.role == AuthorRole.TOOL:
                chat_request_messages.append(Content(role="function", parts=format_tool_message(message)))

        return chat_request_messages

    # endregion

    # region Non-streaming

    def _create_chat_message_content(
        self, response: AsyncGenerateContentResponse, candidate: Candidate
    ) -> ChatMessageContent:
        """Create a chat message content object.

        Args:
            response: The response from the service.
            candidate: The candidate from the response.

        Returns:
            A chat message content object.
        """
        # Best effort conversion of finish reason. The raw value will be available in metadata.
        finish_reason: FinishReason | None = finish_reason_from_google_ai_to_semantic_kernel(candidate.finish_reason)
        response_metadata = self._get_metadata_from_response(response)
        response_metadata.update(self._get_metadata_from_candidate(candidate))

        items: list[CMC_ITEM_TYPES] = []
        for idx, part in enumerate(candidate.content.parts):
            if part.text:
                items.append(TextContent(text=part.text, inner_content=response, metadata=response_metadata))
            elif part.function_call:
                items.append(
                    FunctionCallContent(
                        id=f"{part.function_call.name}_{idx!s}",
                        name=format_gemini_function_name_to_kernel_function_fully_qualified_name(
                            part.function_call.name
                        ),
                        arguments={k: v for k, v in part.function_call.args.items()},
                    )
                )

        return ChatMessageContent(
            ai_model_id=self.ai_model_id,
            role=AuthorRole.ASSISTANT,
            items=items,
            inner_content=response,
            finish_reason=finish_reason,
            metadata=response_metadata,
        )

    # endregion

    # region Streaming

    def _create_streaming_chat_message_content(
        self,
        chunk: GenerateContentResponse,
        candidate: Candidate,
        function_invoke_attempt: int = 0,
    ) -> StreamingChatMessageContent:
        """Create a streaming chat message content object.

        Args:
            chunk: The response from the service.
            candidate: The candidate from the response.
            function_invoke_attempt: The function invoke attempt.

        Returns:
            A streaming chat message content object.
        """
        # Best effort conversion of finish reason. The raw value will be available in metadata.
        finish_reason: FinishReason | None = finish_reason_from_google_ai_to_semantic_kernel(candidate.finish_reason)
        response_metadata = self._get_metadata_from_response(chunk)
        response_metadata.update(self._get_metadata_from_candidate(candidate))

        items: list[STREAMING_ITEM_TYPES] = []
        for idx, part in enumerate(candidate.content.parts):
            if part.text:
                items.append(
                    StreamingTextContent(
                        choice_index=candidate.index,
                        text=part.text,
                        inner_content=chunk,
                        metadata=response_metadata,
                    )
                )
            elif part.function_call:
                items.append(
                    FunctionCallContent(
                        id=f"{part.function_call.name}_{idx!s}",
                        name=format_gemini_function_name_to_kernel_function_fully_qualified_name(
                            part.function_call.name
                        ),
                        arguments={k: v for k, v in part.function_call.args.items()},
                    )
                )

        return StreamingChatMessageContent(
            ai_model_id=self.ai_model_id,
            role=AuthorRole.ASSISTANT,
            choice_index=candidate.index,
            items=items,
            inner_content=chunk,
            finish_reason=finish_reason,
            metadata=response_metadata,
            function_invoke_attempt=function_invoke_attempt,
        )

    # endregion

    def _get_metadata_from_response(
        self, response: AsyncGenerateContentResponse | GenerateContentResponse
    ) -> dict[str, Any]:
        """Get metadata from the response.

        Args:
            response: The response from the service.

        Returns:
            A dictionary containing metadata.
        """
        return {
            "prompt_feedback": response.prompt_feedback,
            "usage": CompletionUsage(
                prompt_tokens=response.usage_metadata.prompt_token_count,
                completion_tokens=response.usage_metadata.candidates_token_count,
            ),
        }

    def _get_metadata_from_candidate(self, candidate: Candidate) -> dict[str, Any]:
        """Get metadata from the candidate.

        Args:
            candidate: The candidate from the response.

        Returns:
            A dictionary containing metadata.
        """
        return {
            "index": candidate.index,
            "finish_reason": candidate.finish_reason,
            "safety_ratings": candidate.safety_ratings,
            "token_count": candidate.token_count,
        }
