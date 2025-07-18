# Copyright (c) Microsoft. All rights reserved.

import sys
from typing import Any

import vertexai
from numpy import array, ndarray
from pydantic import ValidationError
from vertexai.language_models import TextEmbedding, TextEmbeddingModel

from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.ai.google.vertex_ai.services.vertex_ai_base import VertexAIBase
from semantic_kernel.connectors.ai.google.vertex_ai.vertex_ai_prompt_execution_settings import (
    VertexAIEmbeddingPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.google.vertex_ai.vertex_ai_settings import VertexAISettings
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover


class VertexAITextEmbedding(VertexAIBase, EmbeddingGeneratorBase):
    """Vertex AI Text Embedding Service."""

    def __init__(
        self,
        project_id: str | None = None,
        region: str | None = None,
        embedding_model_id: str | None = None,
        service_id: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize the Google Vertex AI Chat Completion Service.

        If no arguments are provided, the service will attempt to load the settings from the environment.
        The following environment variables are used:
        - VERTEX_AI_EMBEDDING_MODEL_ID
        - VERTEX_AI_PROJECT_ID

        Args:
            project_id (str): The Google Cloud project ID.
            region (str): The Google Cloud region.
            embedding_model_id (str): The Gemini model ID.
            service_id (str): The Vertex AI service ID.
            env_file_path (str): The path to the environment file.
            env_file_encoding (str): The encoding of the environment file.
        """
        try:
            vertex_ai_settings = VertexAISettings(
                project_id=project_id,
                region=region,
                embedding_model_id=embedding_model_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as e:
            raise ServiceInitializationError(f"Failed to validate Vertex AI settings: {e}") from e
        if not vertex_ai_settings.embedding_model_id:
            raise ServiceInitializationError("The Vertex AI embedding model ID is required.")

        super().__init__(
            ai_model_id=vertex_ai_settings.embedding_model_id,
            service_id=service_id or vertex_ai_settings.embedding_model_id,
            service_settings=vertex_ai_settings,
        )

    @override
    async def generate_embeddings(
        self,
        texts: list[str],
        settings: "PromptExecutionSettings | None" = None,
        **kwargs: Any,
    ) -> ndarray:
        raw_embeddings = await self.generate_raw_embeddings(texts, settings, **kwargs)
        return array(raw_embeddings)

    @override
    async def generate_raw_embeddings(
        self,
        texts: list[str],
        settings: "PromptExecutionSettings | None" = None,
        **kwargs: Any,
    ) -> list[list[float]]:
        if not settings:
            settings = VertexAIEmbeddingPromptExecutionSettings()
        else:
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, VertexAIEmbeddingPromptExecutionSettings)  # nosec

        vertexai.init(project=self.service_settings.project_id, location=self.service_settings.region)
        model = TextEmbeddingModel.from_pretrained(self.service_settings.embedding_model_id)
        response: list[TextEmbedding] = await model.get_embeddings_async(
            texts,
            **settings.prepare_settings_dict(),
        )

        return [text_embedding.values for text_embedding in response]

    @override
    def get_prompt_execution_settings_class(
        self,
    ) -> type["PromptExecutionSettings"]:
        """Get the request settings class."""
        return VertexAIEmbeddingPromptExecutionSettings
