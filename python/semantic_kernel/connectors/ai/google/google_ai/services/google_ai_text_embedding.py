# Copyright (c) Microsoft. All rights reserved.

import sys
from typing import Any

import google.generativeai as genai
from google.generativeai.types.text_types import BatchEmbeddingDict
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
        service_id: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize the Google AI Text Embedding service.

        If no arguments are provided, the service will attempt to load the settings from the environment.
        The following environment variables are used:
        - GOOGLE_AI_EMBEDDING_MODEL_ID
        - GOOGLE_AI_API_KEY

        Args:
            embedding_model_id (str | None): The embedding model ID. (Optional)
            api_key (str | None): The API key. (Optional)
            service_id (str | None): The service ID. (Optional)
            env_file_path (str | None): The path to the .env file. (Optional)
            env_file_encoding (str | None): The encoding of the .env file. (Optional)

        Raises:
            ServiceInitializationError: If an error occurs during initialization.
        """
        try:
            google_ai_settings = GoogleAISettings(
                embedding_model_id=embedding_model_id,
                api_key=api_key,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as e:
            raise ServiceInitializationError(f"Failed to validate Google AI settings: {e}") from e
        if not google_ai_settings.embedding_model_id:
            raise ServiceInitializationError("The Google AI embedding model ID is required.")

        super().__init__(
            ai_model_id=google_ai_settings.embedding_model_id,
            service_id=service_id or google_ai_settings.embedding_model_id,
            service_settings=google_ai_settings,
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

        genai.configure(api_key=self.service_settings.api_key.get_secret_value())
        if not self.service_settings.embedding_model_id:
            raise ServiceInitializationError("The Google AI embedding model ID is required.")
        response: BatchEmbeddingDict = await genai.embed_content_async(  # type: ignore
            model=self.service_settings.embedding_model_id,
            content=texts,
            **settings.prepare_settings_dict(),
        )

        return response["embedding"]

    @override
    def get_prompt_execution_settings_class(
        self,
    ) -> type["PromptExecutionSettings"]:
        """Get the request settings class."""
        return GoogleAIEmbeddingPromptExecutionSettings
