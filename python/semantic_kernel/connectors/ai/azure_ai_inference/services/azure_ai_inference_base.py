# Copyright (c) Microsoft. All rights reserved.


from abc import ABC
from typing import TypeVar

from azure.ai.inference import load_client as load_client_sync
from azure.ai.inference.aio import ChatCompletionsClient as ChatCompletionsClientAsync
from azure.ai.inference.aio import EmbeddingsClient as EmbeddingsClientAsync
from azure.ai.inference.models import ModelInfo, ModelType
from azure.core.credentials import AzureKeyCredential

from semantic_kernel.connectors.ai.azure_ai_inference.azure_ai_inference_settings import AzureAIInferenceSettings
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError
from semantic_kernel.kernel_pydantic import KernelBaseModel

T = TypeVar("T", bound=ChatCompletionsClientAsync | EmbeddingsClientAsync)


class AzureAIInferenceBase(KernelBaseModel, ABC):
    """Base class for Azure AI Inference services."""

    def _create_client(self, settings: AzureAIInferenceSettings, client_type: type[T]) -> tuple[T, ModelInfo]:
        """Create the Azure AI Inference client.

        Client is created synchronously to check the model type before creating the async client.
        """
        credential = AzureKeyCredential(settings.api_key.get_secret_value())
        sync_client = load_client_sync(endpoint=settings.endpoint, credential=credential)

        model_info = sync_client.get_model_info()
        if model_info.model_type not in self._get_desired_mode_type(client_type):
            raise ServiceInitializationError(
                f"Endpoint {settings.endpoint} does not support the desired client type: {client_type}. "
                f" The provided endpoint is for a {model_info.model_type} model."
            )

        return (
            client_type(endpoint=settings.endpoint, credential=credential),
            model_info,
        )

    def _get_desired_mode_type(self, client_type: type) -> tuple[ModelType, str]:
        """Get the desired model type for the service."""
        if client_type == ChatCompletionsClientAsync:
            return ModelType.CHAT, "completion"
        if client_type == EmbeddingsClientAsync:
            return ModelType.EMBEDDINGS, "embedding"

        raise ServiceInitializationError(f"Client type {client_type} is not supported.")
