# Copyright (c) Microsoft. All rights reserved.


import sys
from collections.abc import AsyncGenerator, AsyncIterable
from typing import Any

import vertexai
from pydantic import ValidationError
from vertexai.generative_models import Candidate, GenerationResponse, GenerativeModel

from semantic_kernel.connectors.ai.google.vertex_ai.services.vertex_ai_base import VertexAIBase
from semantic_kernel.connectors.ai.google.vertex_ai.vertex_ai_prompt_execution_settings import (
    VertexAITextPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.google.vertex_ai.vertex_ai_settings import VertexAISettings
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover


class VertexAITextCompletion(VertexAIBase, TextCompletionClientBase):
    """Vertex AI Text Completion Client."""

    def __init__(
        self,
        project_id: str | None = None,
        region: str | None = None,
        gemini_model_id: str | None = None,
        service_id: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize the Google Vertex AI Text Completion Service.

        If no arguments are provided, the service will attempt to load the settings from the environment.
        The following environment variables are used:
        - VERTEX_AI_GEMINI_MODEL_ID
        - VERTEX_AI_PROJECT_ID

        Args:
            project_id (str): The Google Cloud project ID.
            region (str): The Google Cloud region.
            gemini_model_id (str): The Gemini model ID.
            service_id (str): The Vertex AI service ID.
            env_file_path (str): The path to the environment file.
            env_file_encoding (str): The encoding of the environment file.
        """
        try:
            vertex_ai_settings = VertexAISettings.create(
                project_id=project_id,
                region=region,
                gemini_model_id=gemini_model_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as e:
            raise ServiceInitializationError(f"Failed to validate Vertex AI settings: {e}") from e
        if not vertex_ai_settings.gemini_model_id:
            raise ServiceInitializationError("The Vertex AI Gemini model ID is required.")

        super().__init__(
            ai_model_id=vertex_ai_settings.gemini_model_id,
            service_id=service_id or vertex_ai_settings.gemini_model_id,
            service_settings=vertex_ai_settings,
        )

    # region Non-streaming
    @override
    async def get_text_contents(
        self,
        prompt: str,
        settings: "PromptExecutionSettings",
    ) -> list[TextContent]:
        settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, VertexAITextPromptExecutionSettings)  # nosec

        return await self._send_request(prompt, settings)

    async def _send_request(self, prompt: str, settings: VertexAITextPromptExecutionSettings) -> list[TextContent]:
        """Send a text generation request to the Vertex AI service."""
        vertexai.init(project=self.service_settings.project_id, location=self.service_settings.region)
        model = GenerativeModel(self.service_settings.gemini_model_id)

        response: GenerationResponse = await model.generate_content_async(
            contents=prompt,
            generation_config=settings.prepare_settings_dict(),
        )

        return [self._create_text_content(response, candidate) for candidate in response.candidates]

    def _create_text_content(self, response: GenerationResponse, candidate: Candidate) -> TextContent:
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

    # endregion

    # region Streaming
    @override
    async def get_streaming_text_contents(
        self,
        prompt: str,
        settings: "PromptExecutionSettings",
    ) -> AsyncGenerator[list["StreamingTextContent"], Any]:
        settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, VertexAITextPromptExecutionSettings)  # nosec

        async_generator = self._send_streaming_request(prompt, settings)

        async for text_contents in async_generator:
            yield text_contents

    async def _send_streaming_request(
        self, prompt: str, settings: VertexAITextPromptExecutionSettings
    ) -> AsyncGenerator[list[StreamingTextContent], Any]:
        """Send a text generation request to the Vertex AI service."""
        vertexai.init(project=self.service_settings.project_id, location=self.service_settings.region)
        model = GenerativeModel(self.service_settings.gemini_model_id)

        response: AsyncIterable[GenerationResponse] = await model.generate_content_async(
            contents=prompt,
            generation_config=settings.prepare_settings_dict(),
            stream=True,
        )

        async for chunk in response:
            yield [self._create_streaming_text_content(chunk, candidate) for candidate in chunk.candidates]

    def _create_streaming_text_content(self, chunk: GenerationResponse, candidate: Candidate) -> StreamingTextContent:
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

    # endregion

    def _get_metadata_from_response(self, response: GenerationResponse) -> dict[str, Any]:
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
        }

    @override
    def get_prompt_execution_settings_class(
        self,
    ) -> type["PromptExecutionSettings"]:
        """Get the request settings class."""
        return VertexAITextPromptExecutionSettings
