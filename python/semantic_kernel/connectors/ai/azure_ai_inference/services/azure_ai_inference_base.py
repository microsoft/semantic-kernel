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
from semantic_kernel.utils.experimental_decorator import experimental_class

T = TypeVar("T", bound=ChatCompletionsClientAsync | EmbeddingsClientAsync)


@experimental_class
class AzureAIInferenceBase(KernelBaseModel, ABC):
    """Base class for Azure AI Inference services."""

    def _create_client(self, settings: AzureAIInferenceSettings, client_type: type[T]) -> tuple[T, ModelInfo]:
        """Create the Azure AI Inference client.

        Client is created synchronously to check the model type before creating the async client.
        """
        credential = AzureKeyCredential(settings.api_key.get_secret_value())
        sync_client = load_client_sync(endpoint=settings.endpoint, credential=credential)

        model_info = sync_client.get_model_info()
        if not self._is_model_desired_type(client_type, model_info.model_type):
            raise ServiceInitializationError(
                f"Endpoint {settings.endpoint} does not support the desired client type: {client_type}. "
                f" The provided endpoint is for a {model_info.model_type} model."
            )

        return (
            client_type(endpoint=settings.endpoint, credential=credential),
            model_info,
        )

    def _is_model_desired_type(self, desired_type: type, model_type: ModelType | str) -> bool:
        """Check if the model type is the desired type."""
        if desired_type == ChatCompletionsClientAsync:
            return model_type in (ModelType.CHAT, "completion")
        if desired_type == EmbeddingsClientAsync:
            return model_type in (ModelType.EMBEDDINGS, "embedding")

        raise ServiceInitializationError(f"Client type {desired_type} is not supported.")
