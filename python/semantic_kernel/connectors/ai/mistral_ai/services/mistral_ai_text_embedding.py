# Copyright (c) Microsoft. All rights reserved.

import sys

if sys.version_info >= (3, 12):
    from typing import Any, override  # pragma: no cover
else:
    from typing_extensions import Any, override  # pragma: no cover

import logging

from mistralai import Mistral
from mistralai.models import EmbeddingResponse
from numpy import array, ndarray
from pydantic import ValidationError

from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.ai.mistral_ai.services.mistral_ai_base import MistralAIBase
from semantic_kernel.connectors.ai.mistral_ai.settings.mistral_ai_settings import MistralAISettings
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError, ServiceResponseException
from semantic_kernel.utils.feature_stage_decorator import experimental

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class MistralAITextEmbedding(MistralAIBase, EmbeddingGeneratorBase):
    """Mistral AI Inference Text Embedding Service."""

    def __init__(
        self,
        ai_model_id: str | None = None,
        api_key: str | None = None,
        service_id: str | None = None,
        async_client: Mistral | None = None,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initialize the Mistral AI Text Embedding service.

        If no arguments are provided, the service will attempt to load the settings from the environment.
        The following environment variables are used:
        - MISTRALAI_API_KEY
        - MISTRALAI_EMBEDDING_MODEL_ID

        Args:
            ai_model_id: : A string that is used to identify the model such as the model name.
            api_key : The API key for the Mistral AI service deployment.
            service_id : Service ID for the embedding completion service.
            async_client : The Mistral AI client to use.
            env_file_path : The path to the environment file.
            env_file_encoding : The encoding of the environment file.

        Raises:
            ServiceInitializationError: If an error occurs during initialization.
        """
        try:
            mistralai_settings = MistralAISettings(
                api_key=api_key,
                embedding_model_id=ai_model_id,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as e:
            raise ServiceInitializationError(f"Failed to validate Mistral AI settings: {e}") from e

        if not mistralai_settings.embedding_model_id:
            raise ServiceInitializationError("The MistralAI embedding model ID is required.")

        if not async_client:
            async_client = Mistral(
                api_key=mistralai_settings.api_key.get_secret_value(),
            )
        super().__init__(
            service_id=service_id or mistralai_settings.embedding_model_id,
            ai_model_id=ai_model_id or mistralai_settings.embedding_model_id,
            async_client=async_client,
        )

    @override
    async def generate_embeddings(
        self,
        texts: list[str],
        settings: "PromptExecutionSettings | None" = None,
        **kwargs: Any,
    ) -> ndarray:
        embedding_response = await self.generate_raw_embeddings(texts, settings, **kwargs)
        return array(embedding_response)

    @override
    async def generate_raw_embeddings(
        self,
        texts: list[str],
        settings: "PromptExecutionSettings | None" = None,
        **kwargs: Any,
    ) -> Any:
        """Generate embeddings from the Mistral AI service."""
        try:
            embedding_response = await self.async_client.embeddings.create_async(model=self.ai_model_id, inputs=texts)
        except Exception as ex:
            raise ServiceResponseException(
                f"{type(self)} service failed to complete the embedding request.",
                ex,
            ) from ex
        if isinstance(embedding_response, EmbeddingResponse):
            return [item.embedding for item in embedding_response.data]
        return []
