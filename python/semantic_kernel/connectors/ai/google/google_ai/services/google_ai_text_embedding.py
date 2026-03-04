# Copyright (c) Microsoft. All rights reserved.

import sys
from typing import Any

from google.genai import Client
from google.genai.types import EmbedContentConfigDict, EmbedContentResponse
from numpy import array, ndarray
from pydantic import ValidationError

from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.ai.google.google_ai.google_ai_prompt_execution_settings import (
    GoogleAIEmbeddingPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.google.google_ai.google_ai_settings import GoogleAISettings
from semantic_kernel.connectors.ai.google.google_ai.services.google_ai_base import GoogleAIBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover


class GoogleAITextEmbedding(GoogleAIBase, EmbeddingGeneratorBase):
    """Google AI Text Embedding Service."""

    def __init__(
        self,
        embedding_model_id: str | None = None,
        api_key: str | None = None,
        project_id: str | None = None,
        region: str | None = None,
        use_vertexai: bool | None = None,
        service_id: str | None = None,
        client: Client | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize the Google AI Text Embedding service.

        If no arguments are provided, the service will attempt to load the settings from the environment.
        The following environment variables are used:
        - GOOGLE_AI_EMBEDDING_MODEL_ID
        - GOOGLE_AI_API_KEY
        - GOOGLE_AI_CLOUD_PROJECT_ID
        - GOOGLE_AI_CLOUD_REGION
        - GOOGLE_AI_USE_VERTEXAI

        Args:
            embedding_model_id (str | None): The embedding model ID. (Optional)
            api_key (str | None): The API key. (Optional)
            project_id (str | None): The Google Cloud project ID. (Optional)
            region (str | None): The Google Cloud region. (Optional)
            use_vertexai (bool | None): Whether to use Vertex AI. (Optional)
            service_id (str | None): The service ID. (Optional)
            client (Client | None): The Google AI Client to use for break glass scenarios. (Optional)
            env_file_path (str | None): The path to the .env file. (Optional)
            env_file_encoding (str | None): The encoding of the .env file. (Optional)

        Raises:
            ServiceInitializationError: If an error occurs during initialization.
        """
        try:
            google_ai_settings = GoogleAISettings(
                embedding_model_id=embedding_model_id,
                api_key=api_key,
                cloud_project_id=project_id,
                cloud_region=region,
                use_vertexai=use_vertexai,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as e:
            raise ServiceInitializationError(f"Failed to validate Google AI settings: {e}") from e

        if not google_ai_settings.embedding_model_id:
            raise ServiceInitializationError("The Google AI embedding model ID is required.")

        if not client:
            if google_ai_settings.use_vertexai and not google_ai_settings.cloud_project_id:
                raise ServiceInitializationError("Project ID must be provided when use_vertexai is True.")
            if not google_ai_settings.use_vertexai and not google_ai_settings.api_key:
                raise ServiceInitializationError("The API key is required when use_vertexai is False.")

        super().__init__(
            ai_model_id=google_ai_settings.embedding_model_id,
            service_id=service_id or google_ai_settings.embedding_model_id,
            service_settings=google_ai_settings,
            client=client,
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
            settings = GoogleAIEmbeddingPromptExecutionSettings()
        else:
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, GoogleAIEmbeddingPromptExecutionSettings)  # nosec

        if not self.service_settings.embedding_model_id:
            raise ServiceInitializationError("The Google AI embedding model ID is required.")

        async def _embed_content(client: Client) -> EmbedContentResponse:
            return await client.aio.models.embed_content(
                model=self.service_settings.embedding_model_id,  # type: ignore[arg-type]
                contents=texts,  # type: ignore[arg-type]
                config=EmbedContentConfigDict(output_dimensionality=settings.output_dimensionality),
            )

        if self.client:
            response: EmbedContentResponse = await _embed_content(self.client)
        elif self.service_settings.use_vertexai:
            with Client(
                vertexai=True,
                project=self.service_settings.cloud_project_id,
                location=self.service_settings.cloud_region,
            ) as client:
                response: EmbedContentResponse = await _embed_content(client)  # type: ignore[no-redef]
        else:
            with Client(api_key=self.service_settings.api_key.get_secret_value()) as client:  # type: ignore[union-attr]
                response: EmbedContentResponse = await _embed_content(client)  # type: ignore[no-redef]

        return [embedding.values for embedding in response.embeddings]  # type: ignore

    @override
    def get_prompt_execution_settings_class(
        self,
    ) -> type["PromptExecutionSettings"]:
        """Get the request settings class."""
        return GoogleAIEmbeddingPromptExecutionSettings
