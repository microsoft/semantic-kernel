# Copyright (c) Microsoft. All rights reserved.

import sys
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

import google.generativeai as genai
from google.generativeai import GenerativeModel
from google.generativeai.protos import Candidate
from google.generativeai.types import AsyncGenerateContentResponse, GenerateContentResponse, GenerationConfig
from pydantic import ValidationError

from semantic_kernel.connectors.ai.completion_usage import CompletionUsage
from semantic_kernel.connectors.ai.google.google_ai.google_ai_prompt_execution_settings import (
    GoogleAITextPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.google.google_ai.google_ai_settings import GoogleAISettings
from semantic_kernel.connectors.ai.google.google_ai.services.google_ai_base import GoogleAIBase
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.contents import TextContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError
from semantic_kernel.utils.telemetry.model_diagnostics.decorators import (
    trace_streaming_text_completion,
    trace_text_completion,
)

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover


class GoogleAITextCompletion(GoogleAIBase, TextCompletionClientBase):
    """Google AI Text Completion Client."""

    def __init__(
        self,
        gemini_model_id: str | None = None,
        api_key: str | None = None,
        service_id: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize the Google AI Text Completion Client.

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
        return GoogleAITextPromptExecutionSettings

    @override
    @trace_text_completion(GoogleAIBase.MODEL_PROVIDER_NAME)
    async def _inner_get_text_contents(
        self,
        prompt: str,
        settings: "PromptExecutionSettings",
    ) -> list[TextContent]:
        if not isinstance(settings, GoogleAITextPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, GoogleAITextPromptExecutionSettings)  # nosec

        genai.configure(api_key=self.service_settings.api_key.get_secret_value())
        if not self.service_settings.gemini_model_id:
            raise ServiceInitializationError("The Google AI Gemini model ID is required.")
        model = GenerativeModel(
            model_name=self.service_settings.gemini_model_id,
        )

        response: AsyncGenerateContentResponse = await model.generate_content_async(
            contents=prompt,
            generation_config=GenerationConfig(**settings.prepare_settings_dict()),
        )

        return [self._create_text_content(response, candidate) for candidate in response.candidates]

    @override
    @trace_streaming_text_completion(GoogleAIBase.MODEL_PROVIDER_NAME)
    async def _inner_get_streaming_text_contents(
        self,
        prompt: str,
        settings: "PromptExecutionSettings",
    ) -> AsyncGenerator[list[StreamingTextContent], Any]:
        if not isinstance(settings, GoogleAITextPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, GoogleAITextPromptExecutionSettings)  # nosec

        genai.configure(api_key=self.service_settings.api_key.get_secret_value())
        if not self.service_settings.gemini_model_id:
            raise ServiceInitializationError("The Google AI Gemini model ID is required.")
        model = GenerativeModel(
            model_name=self.service_settings.gemini_model_id,
        )

        response: AsyncGenerateContentResponse = await model.generate_content_async(
            contents=prompt,
            generation_config=GenerationConfig(**settings.prepare_settings_dict()),
            stream=True,
        )

        async for chunk in response:
            yield [self._create_streaming_text_content(chunk, candidate) for candidate in chunk.candidates]

    # endregion

    def _create_text_content(self, response: AsyncGenerateContentResponse, candidate: Candidate) -> TextContent:
        """Create a text content object.

        Args:
            response: The response from the service.
            candidate: The candidate from the response.

        Returns:
            A text content object.
        """
        response_metadata = self._get_metadata_from_response(response)
        response_metadata.update(self._get_metadata_from_candidate(candidate))

        return TextContent(
            ai_model_id=self.ai_model_id,
            text=candidate.content.parts[0].text,
            inner_content=response,
            metadata=response_metadata,
        )

    def _create_streaming_text_content(
        self, chunk: GenerateContentResponse, candidate: Candidate
    ) -> StreamingTextContent:
        """Create a streaming text content object.

        Args:
            chunk: The response from the service.
            candidate: The candidate from the response.

        Returns:
            A streaming text content object.
        """
        response_metadata = self._get_metadata_from_response(chunk)
        response_metadata.update(self._get_metadata_from_candidate(candidate))

        return StreamingTextContent(
            ai_model_id=self.ai_model_id,
            choice_index=candidate.index,
            text=candidate.content.parts[0].text,
            inner_content=chunk,
            metadata=response_metadata,
        )

    def _get_metadata_from_response(
        self,
        response: AsyncGenerateContentResponse | GenerateContentResponse,
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
