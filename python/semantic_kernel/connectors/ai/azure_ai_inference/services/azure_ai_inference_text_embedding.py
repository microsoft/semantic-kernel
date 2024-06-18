# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from azure.ai.inference import load_client as load_client_sync
from azure.ai.inference.aio import EmbeddingsClient as EmbeddingsClientAsync
from azure.ai.inference.models import EmbeddingsResult, ModelInfo, ModelType
from azure.core.credentials import AzureKeyCredential
from numpy import array, ndarray
from pydantic import ValidationError

from semantic_kernel.connectors.ai.azure_ai_inference.azure_ai_inference_prompt_execution_settings import (
    AzureAIInferenceEmbeddingPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.azure_ai_inference.azure_ai_inference_settings import AzureAIInferenceSettings
from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError


class AzureAIInferenceTextEmbedding(EmbeddingGeneratorBase):
    """Azure AI Inference Text Embedding Service."""

    client: EmbeddingsClientAsync

    def __init__(
        self,
        api_key: str | None = None,
        endpoint: str | None = None,
        service_id: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        client: EmbeddingsClientAsync | None = None,
        model_info: ModelInfo | None = None,
    ) -> None:
        """Initialize the Azure AI Inference Text Embedding service.

        Args:
            api_key: The API key for the Azure AI Inference service deployment.
            endpoint: The endpoint of the Azure AI Inference service deployment.
            service_id: Service ID for the chat completion service. (Optional)
            env_file_path: The path to the environment file. (Optional)
            env_file_encoding: The encoding of the environment file. (Optional)
            client: The Azure AI Inference client to use. (Optional)
            model_info: The model info of the provided client. (Optional, required if client is provided)
        """
        if client is not None:
            if model_info is None:
                raise ServiceInitializationError("Model info is required when providing a client.")
        else:
            try:
                azure_ai_inference_settings = AzureAIInferenceSettings.create(
                    api_key=api_key,
                    endpoint=endpoint,
                    env_file_path=env_file_path,
                    env_file_encoding=env_file_encoding,
                )
            except ValidationError as e:
                raise ServiceInitializationError(f"Failed to validate Azure AI Inference settings: {e}") from e

            client, model_info = self._create_client(azure_ai_inference_settings)

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

        return array([item.embedding for item in response.data])

    def _create_client(
        self, azure_ai_inference_settings: AzureAIInferenceSettings
    ) -> tuple[EmbeddingsClientAsync, ModelInfo]:
        """Create the Azure AI Inference client.

        Client is created synchronously to check the model type before creating the async client.
        """
        embedding_client_sync = load_client_sync(
            endpoint=azure_ai_inference_settings.endpoint,
            credential=AzureKeyCredential(azure_ai_inference_settings.api_key.get_secret_value()),
        )

        model_info = embedding_client_sync.get_model_info()
        if model_info.model_type not in (ModelType.EMBEDDINGS, "embedding"):
            raise ServiceInitializationError(
                f"Endpoint {azure_ai_inference_settings.endpoint} does not support text embedding generation. "
                f"The provided endpoint is for a {model_info.model_type} model."
            )

        return (
            EmbeddingsClientAsync(
                endpoint=azure_ai_inference_settings.endpoint,
                credential=AzureKeyCredential(azure_ai_inference_settings.api_key.get_secret_value()),
            ),
            model_info,
        )
