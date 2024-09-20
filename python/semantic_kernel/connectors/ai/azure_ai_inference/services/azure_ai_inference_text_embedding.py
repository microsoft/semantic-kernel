# Copyright (c) Microsoft. All rights reserved.

import sys
from typing import TYPE_CHECKING, Any

from azure.ai.inference.aio import EmbeddingsClient
from azure.ai.inference.models import EmbeddingsResult
from azure.core.credentials import AzureKeyCredential
from numpy import array, ndarray
from pydantic import ValidationError

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from azure.identity import DefaultAzureCredential

from semantic_kernel.connectors.ai.azure_ai_inference.azure_ai_inference_prompt_execution_settings import (
    AzureAIInferenceEmbeddingPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.azure_ai_inference.azure_ai_inference_settings import AzureAIInferenceSettings
from semantic_kernel.connectors.ai.azure_ai_inference.services.azure_ai_inference_base import AzureAIInferenceBase
from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.ai.open_ai.const import DEFAULT_AZURE_API_VERSION
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError
from semantic_kernel.utils.experimental_decorator import experimental_class
from semantic_kernel.utils.telemetry.user_agent import SEMANTIC_KERNEL_USER_AGENT

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


@experimental_class
class AzureAIInferenceTextEmbedding(EmbeddingGeneratorBase, AzureAIInferenceBase):
    """Azure AI Inference Text Embedding Service."""

    def __init__(
        self,
        ai_model_id: str,
        api_key: str | None = None,
        endpoint: str | None = None,
        service_id: str | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        client: EmbeddingsClient | None = None,
    ) -> None:
        """Initialize the Azure AI Inference Text Embedding service.

        If no arguments are provided, the service will attempt to load the settings from the environment.
        The following environment variables are used:
        - AZURE_AI_INFERENCE_API_KEY
        - AZURE_AI_INFERENCE_ENDPOINT

        Args:
            ai_model_id: (str): A string that is used to identify the model such as the model name. (Required)
            api_key (str | None): The API key for the Azure AI Inference service deployment. (Optional)
            endpoint (str | None): The endpoint of the Azure AI Inference service deployment. (Optional)
            service_id (str | None): Service ID for the chat completion service. (Optional)
            env_file_path (str | None): The path to the environment file. (Optional)
            env_file_encoding (str | None): The encoding of the environment file. (Optional)
            client (EmbeddingsClient | None): The Azure AI Inference client to use. (Optional)

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

            endpoint = str(azure_ai_inference_settings.endpoint)
            if azure_ai_inference_settings.api_key is not None:
                client = EmbeddingsClient(
                    endpoint=endpoint,
                    credential=AzureKeyCredential(azure_ai_inference_settings.api_key.get_secret_value()),
                    user_agent=SEMANTIC_KERNEL_USER_AGENT,
                )
            else:
                # Try to create the client with a DefaultAzureCredential
                client = EmbeddingsClient(
                    endpoint=endpoint,
                    credential=DefaultAzureCredential(),
                    credential_scopes=["https://cognitiveservices.azure.com/.default"],
                    api_version=DEFAULT_AZURE_API_VERSION,
                    user_agent=SEMANTIC_KERNEL_USER_AGENT,
                )

        super().__init__(
            ai_model_id=ai_model_id,
            service_id=service_id or ai_model_id,
            client=client,
        )

    async def generate_embeddings(
        self,
        texts: list[str],
        settings: "PromptExecutionSettings | None" = None,
        **kwargs: Any,
    ) -> ndarray:
        """Generate embeddings from the Azure AI Inference service."""
        if not settings:
            settings = AzureAIInferenceEmbeddingPromptExecutionSettings()
        else:
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, AzureAIInferenceEmbeddingPromptExecutionSettings)  # nosec
        assert isinstance(self.client, EmbeddingsClient)  # nosec

        response: EmbeddingsResult = await self.client.embed(
            input=texts,
            model_extras=settings.extra_parameters if settings else None,
            dimensions=settings.dimensions if settings else None,
            encoding_format=settings.encoding_format if settings else None,
            input_type=settings.input_type if settings else None,
        )

        return array([array(item.embedding) for item in response.data])

    @override
    def get_prompt_execution_settings_class(
        self,
    ) -> type["PromptExecutionSettings"]:
        """Get the request settings class."""
        return AzureAIInferenceEmbeddingPromptExecutionSettings
