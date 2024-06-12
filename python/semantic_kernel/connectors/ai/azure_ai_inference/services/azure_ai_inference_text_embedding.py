# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Any

from azure.ai.inference.aio import EmbeddingsClient, load_client
from azure.ai.inference.models import (
    EmbeddingsResult,
    ModelInfo,
    ModelType,
)
from azure.core.credentials import AzureKeyCredential
from numpy import array, ndarray
from pydantic import ValidationError

from semantic_kernel.connectors.ai.azure_ai_inference.azure_ai_inference_prompt_execution_settings import (
    AzureAIInferenceEmbeddingPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.azure_ai_inference.azure_ai_inference_settings import (
    AzureAIInferenceSettings,
)
from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import (
    EmbeddingGeneratorBase,
)
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError


class AzureAIInferenceTextEmbedding(EmbeddingGeneratorBase):
    """Azure AI Inference Text Embedding Service."""

    client: EmbeddingsClient

    def __init__(
        self,
        api_key: str | None = None,
        endpoint: str | None = None,
        service_id: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize the Azure AI Inference Text Embedding service.

        Args:
            api_key: The API key for the Azure AI Inference service deployment.
            endpoint: The endpoint of the Azure AI Inference service deployment.
            service_id: Service ID for the chat completion service. (Optional)
            env_file_path: The path to the environment file. (Optional)
            env_file_encoding: The encoding of the environment file. (Optional)
        """
        try:
            azure_ai_inference_settings = AzureAIInferenceSettings.create(
                api_key=api_key,
                endpoint=endpoint,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as e:
            raise ServiceInitializationError(
                f"Failed to validate Azure AI Inference settings: {e}"
            ) from e

        client, model_info = self._create_client(azure_ai_inference_settings)
        if model_info.model_type not in (ModelType.EMBEDDINGS, "embedding"):
            raise ServiceInitializationError(
                f"Endpoint {azure_ai_inference_settings.endpoint} does not support text embedding. "
                f"The provided endpoint is for a {model_info.model_type} model."
            )

        super().__init__(
            ai_model_id=model_info.model_name,
            endpoint=azure_ai_inference_settings.endpoint,
            api_key=azure_ai_inference_settings.api_key,
            service_id=service_id or model_info.model_name,
            client=client,
        )

    async def generate_embeddings(self, texts: list[str], **kwargs: Any) -> ndarray:
        """Generate embeddings from the Azure AI Inference service."""
        settings: AzureAIInferenceEmbeddingPromptExecutionSettings = kwargs.get(
            "settings", None
        )
        response: EmbeddingsResult = await self.client.embed(
            input=texts,
            model_extras=settings.extra_parameters if settings else None,
            dimensions=settings.dimensions if settings else None,
            encoding_format=settings.encoding_format if settings else None,
            input_type=settings.input_type if settings else None,
        )

        return array([item.embedding for item in response.data])

    def _create_client(
        self, azure_ai_inference_settings: AzureAIInferenceSettings
    ) -> tuple[EmbeddingsClient, ModelInfo]:
        loop = asyncio.get_event_loop()

        # Create the client
        task = loop.create_task(
            load_client(
                endpoint=azure_ai_inference_settings.endpoint,
                credential=AzureKeyCredential(
                    azure_ai_inference_settings.api_key.get_secret_value()
                ),
            )
        )
        loop.run_until_complete(task)
        client = task.result()

        # Get the model info
        task = loop.create_task(client.get_model_info())
        loop.run_until_complete(task)
        model_info = task.result()

        loop.close()

        return (client, model_info)
