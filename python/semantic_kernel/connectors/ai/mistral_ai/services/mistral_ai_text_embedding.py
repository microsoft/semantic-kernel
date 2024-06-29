# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from mistralai.async_client import MistralAsyncClient
from mistralai.models.embeddings import EmbeddingResponse
from numpy import array, ndarray
from pydantic import ValidationError

from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.ai.mistral_ai.settings.mistral_ai_settings import MistralAISettings
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class MistralAITextEmbedding(EmbeddingGeneratorBase):
    """Mistral AI Inference Text Embedding Service."""

    client: MistralAsyncClient | None = None,

    def __init__(
        self,
        ai_model_id: str | None = None,
        api_key: str | None = None,
        service_id: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        client: MistralAsyncClient | None = None,
    ) -> None:
        """Initialize the Mistral AI Text Embedding service.

        If no arguments are provided, the service will attempt to load the settings from the environment.
        The following environment variables are used:
        - MISTRALAI_API_KEY
        - MISTRALAI_EMBEDDING_MODEL_ID

        Args:
            ai_model_id: (str): A string that is used to identify the model such as the model name. (Required)
            api_key (str | None): The API key for the Mistral AI service deployment. (Optional)
            service_id (str | None): Service ID for the embedding completion service. (Optional)
            env_file_path (str | None): The path to the environment file. (Optional)
            env_file_encoding (str | None): The encoding of the environment file. (Optional)
            client (MistralAsyncClient | None): The Mistral AI client to use. (Optional)

        Raises:
            ServiceInitializationError: If an error occurs during initialization.
        """
        try:
            mistralai_settings = MistralAISettings.create(
                api_key=api_key,
                embedding_model_id=ai_model_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as e:
            raise ServiceInitializationError(f"Failed to validate Mistral AI settings: {e}") from e

        if not client:
            client = MistralAsyncClient(
                api_key=mistralai_settings.api_key.get_secret_value()
            )

        super().__init__(
            service_id=service_id or mistralai_settings.embedding_model_id,
            ai_model_id=ai_model_id or mistralai_settings.embedding_model_id,
            client=client,
        )

    async def generate_embeddings(self, texts: list[str], **kwargs: Any) -> ndarray:
        """Generate embeddings from the Mistral AI service."""
        response: EmbeddingResponse = await self.client.embeddings(
            model=self.ai_model_id,
            input=texts
        )

        return array([array(item.embedding) for item in response.data])
