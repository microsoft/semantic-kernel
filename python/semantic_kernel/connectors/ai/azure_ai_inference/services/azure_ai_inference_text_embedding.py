# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from azure.ai.inference.aio import EmbeddingsClient
from azure.ai.inference.models import EmbeddingsResult, ModelInfo
from numpy import array, ndarray
from pydantic import ValidationError

from semantic_kernel.connectors.ai.azure_ai_inference.azure_ai_inference_prompt_execution_settings import (
    AzureAIInferenceEmbeddingPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.azure_ai_inference.azure_ai_inference_settings import AzureAIInferenceSettings
from semantic_kernel.connectors.ai.azure_ai_inference.services.azure_ai_inference_base import AzureAIInferenceBase
from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class AzureAIInferenceTextEmbedding(EmbeddingGeneratorBase, AzureAIInferenceBase):
    """Azure AI Inference Text Embedding Service."""

    client: EmbeddingsClient

    def __init__(
        self,
        api_key: str | None = None,
        endpoint: str | None = None,
        service_id: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        client: EmbeddingsClient | None = None,
        model_info: ModelInfo | None = None,
    ) -> None:
        """Initialize the Azure AI Inference Text Embedding service.

        If no arguments are provided, the service will attempt to load the settings from the environment.
        The following environment variables are used:
        - AZURE_AI_INFERENCE_API_KEY
        - AZURE_AI_INFERENCE_ENDPOINT

        Args:
            api_key (str | None): The API key for the Azure AI Inference service deployment. (Optional)
            endpoint (str | None): The endpoint of the Azure AI Inference service deployment. (Optional)
            service_id (str | None): Service ID for the chat completion service. (Optional)
            env_file_path (str | None): The path to the environment file. (Optional)
            env_file_encoding (str | None): The encoding of the environment file. (Optional)
            client (EmbeddingsClient | None): The Azure AI Inference client to use. (Optional)
            model_info (ModelInfo | None): The model info of the provided client. (Optional, required if client is
                provided)

        Raises:
            ServiceInitializationError: If an error occurs during initialization.
        """
        if not client:
            try:
                azure_ai_inference_settings = AzureAIInferenceSettings.create(
                    api_key=api_key,
                    endpoint=endpoint,
                    env_file_path=env_file_path,
                    env_file_encoding=env_file_encoding,
                )
            except ValidationError as e:
                raise ServiceInitializationError(f"Failed to validate Azure AI Inference settings: {e}") from e

            client, model_info = self._create_client(azure_ai_inference_settings, EmbeddingsClient)
        elif not model_info:
            raise ServiceInitializationError("Model info is required when providing a client.")

        super().__init__(
            ai_model_id=model_info.model_name,
            service_id=service_id or model_info.model_name,
            client=client,
        )

    async def generate_embeddings(self, texts: list[str], **kwargs: Any) -> ndarray:
        """Generate embeddings from the Azure AI Inference service."""
        settings: AzureAIInferenceEmbeddingPromptExecutionSettings = kwargs.get("settings", None)
        response: EmbeddingsResult = await self.client.embed(
            input=texts,
            model_extras=settings.extra_parameters if settings else None,
            dimensions=settings.dimensions if settings else None,
            encoding_format=settings.encoding_format if settings else None,
            input_type=settings.input_type if settings else None,
            kwargs=kwargs,
        )

        return array([array(item.embedding) for item in response.data])
