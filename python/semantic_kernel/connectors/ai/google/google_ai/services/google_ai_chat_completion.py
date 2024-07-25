# Copyright (c) Microsoft. All rights reserved.


import sys
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

import google.generativeai as genai
from google.generativeai import GenerativeModel
from google.generativeai.protos import Candidate, Content
from google.generativeai.types import AsyncGenerateContentResponse, GenerateContentResponse, GenerationConfig
from pydantic import ValidationError

from semantic_kernel.connectors.ai.google.google_ai.google_ai_prompt_execution_settings import (
    GoogleAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.google.google_ai.services.google_ai_base import GoogleAIBase
from semantic_kernel.connectors.ai.google.google_ai.services.utils import (
    filter_system_message,
    finish_reason_from_google_ai_to_semantic_kernel,
    format_assistant_message,
    format_user_message,
)
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.google.google_ai.google_ai_settings import GoogleAISettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


class GoogleAIChatCompletion(GoogleAIBase, ChatCompletionClientBase):
    """Google AI Chat Completion Client."""

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
            google_ai_settings = GoogleAISettings.create(
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

    # region Non-streaming
    @override
    async def get_chat_message_contents(
        self,
        chat_history: ChatHistory,
        settings: "PromptExecutionSettings",
        **kwargs: Any,
    ) -> list[ChatMessageContent]:
        settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, GoogleAIChatPromptExecutionSettings)  # nosec

        return await self._send_chat_request(chat_history, settings)

    async def _send_chat_request(
        self, chat_history: ChatHistory, settings: GoogleAIChatPromptExecutionSettings
    ) -> list[ChatMessageContent]:
        """Send a chat request to the Google AI service."""
        genai.configure(api_key=self.service_settings.api_key.get_secret_value())
        model = GenerativeModel(
            self.service_settings.gemini_model_id,
            system_instruction=filter_system_message(chat_history),
        )

        response: AsyncGenerateContentResponse = await model.generate_content_async(
            contents=self._prepare_chat_history_for_request(chat_history),
            generation_config=GenerationConfig(**settings.prepare_settings_dict()),
        )

        return [self._create_chat_message_content(response, candidate) for candidate in response.candidates]

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

        return ChatMessageContent(
            ai_model_id=self.ai_model_id,
            role=AuthorRole.ASSISTANT,
            content=candidate.content.parts[0].text,
            inner_content=response,
            finish_reason=finish_reason,
            metadata=response_metadata,
        )

    # endregion

    # region Streaming
    @override
    async def get_streaming_chat_message_contents(
        self,
        chat_history: ChatHistory,
        settings: "PromptExecutionSettings",
        **kwargs: Any,
    ) -> AsyncGenerator[list[StreamingChatMessageContent], Any]:
        settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, GoogleAIChatPromptExecutionSettings)  # nosec

        async_generator = self._send_chat_streaming_request(chat_history, settings)

        async for messages in async_generator:
            yield messages

    async def _send_chat_streaming_request(
        self,
        chat_history: ChatHistory,
        settings: GoogleAIChatPromptExecutionSettings,
    ) -> AsyncGenerator[list[StreamingChatMessageContent], Any]:
        """Send a streaming chat request to the Google AI service."""
        genai.configure(api_key=self.service_settings.api_key.get_secret_value())
        model = GenerativeModel(
            self.service_settings.gemini_model_id,
            system_instruction=filter_system_message(chat_history),
        )

        response: AsyncGenerateContentResponse = await model.generate_content_async(
            contents=self._prepare_chat_history_for_request(chat_history),
            generation_config=GenerationConfig(**settings.prepare_settings_dict()),
            stream=True,
        )

        async for chunk in response:
            yield [self._create_streaming_chat_message_content(chunk, candidate) for candidate in chunk.candidates]

    def _create_streaming_chat_message_content(
        self,
        chunk: GenerateContentResponse,
        candidate: Candidate,
    ) -> StreamingChatMessageContent:
        """Create a streaming chat message content object.

        Args:
            chunk: The response from the service.
            candidate: The candidate from the response.

        Returns:
            A streaming chat message content object.
        """
        # Best effort conversion of finish reason. The raw value will be available in metadata.
        finish_reason: FinishReason | None = finish_reason_from_google_ai_to_semantic_kernel(candidate.finish_reason)
        response_metadata = self._get_metadata_from_response(chunk)
        response_metadata.update(self._get_metadata_from_candidate(candidate))

        return StreamingChatMessageContent(
            ai_model_id=self.ai_model_id,
            role=AuthorRole.ASSISTANT,
            choice_index=candidate.index,
            content=candidate.content.parts[0].text,
            inner_content=chunk,
            finish_reason=finish_reason,
            metadata=response_metadata,
        )

    # endregion

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
            else:
                raise ValueError(f"Unsupported role: {message.role}")

        return chat_request_messages

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
            "usage": response.usage_metadata,
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

    @override
    def get_prompt_execution_settings_class(
        self,
    ) -> type["PromptExecutionSettings"]:
        """Get the request settings class."""
        return GoogleAIChatPromptExecutionSettings
