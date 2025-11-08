# Copyright (c) Microsoft. All rights reserved.

import sys
from typing import TYPE_CHECKING, Any

from numpy import array, ndarray

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.ai.voyage_ai.services.voyage_ai_base import VoyageAIBase
from semantic_kernel.connectors.ai.voyage_ai.voyage_ai_prompt_execution_settings import (
    VoyageAIContextualizedEmbeddingPromptExecutionSettings,
)
from semantic_kernel.exceptions.service_exceptions import (
    ServiceInitializationError,
    ServiceResponseException,
)

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


class VoyageAIContextualizedEmbedding(VoyageAIBase, EmbeddingGeneratorBase):
    """VoyageAI Contextualized Embedding Service.

    Generates embeddings that capture both local chunk details and
    global document-level metadata using the voyage-context-3 model.

    Note: Contextualized embeddings do not support truncation. Inputs that
    exceed the model's context length will be rejected.
    """

    def __init__(
        self,
        ai_model_id: str | None = None,
        service_id: str | None = None,
        api_key: str | None = None,
        client: Any | None = None,
        env_file_path: str | None = None,
        endpoint: str | None = None,
    ):
        """Initialize VoyageAI contextualized embedding service.

        Args:
            ai_model_id: The VoyageAI model ID (required).
            service_id: The service ID (optional).
            api_key: The VoyageAI API key (optional).
            client: A pre-configured VoyageAI client (optional).
            env_file_path: Path to .env file (optional).
            endpoint: VoyageAI API endpoint (optional).
        """
        # Use contextualized model from settings if not provided
        if not ai_model_id:
            from semantic_kernel.connectors.ai.voyage_ai.voyage_ai_settings import VoyageAISettings

            settings = VoyageAISettings.create(env_file_path=env_file_path)
            ai_model_id = settings.contextualized_embedding_model_id

        if not ai_model_id:
            raise ServiceInitializationError(
                "No model ID provided. Set ai_model_id parameter or "
                "VOYAGE_AI_CONTEXTUALIZED_EMBEDDING_MODEL_ID environment variable."
            )

        super().__init__(
            ai_model_id=ai_model_id,
            service_id=service_id,
            api_key=api_key,
            client=client,
            env_file_path=env_file_path,
            endpoint=endpoint,
        )

    async def generate_contextualized_embeddings(
        self,
        inputs: list[list[str]],
        settings: "PromptExecutionSettings | None" = None,
        **kwargs: Any,
    ) -> ndarray:
        """Generate contextualized embeddings for the given inputs.

        Args:
            inputs: List of lists where each inner list contains document chunks.
                   Example: [["chunk1", "chunk2"], ["doc2_chunk1"]]
            settings: Prompt execution settings (optional).
            kwargs: Additional arguments to pass to the request.

        Returns:
            ndarray: Array of contextualized embeddings.
        """
        if not settings:
            settings = VoyageAIContextualizedEmbeddingPromptExecutionSettings()
        else:
            settings = self.get_prompt_execution_settings_from_settings(settings)

        try:
            # Call VoyageAI contextualized embeddings API
            response = await self.aclient.contextualized_embed(
                inputs=inputs,
                model=self.ai_model_id,
                **settings.prepare_settings_dict(),
            )

            # Extract embeddings from all results
            # The response structure: response.results is a list where each result
            # contains a list of embeddings (not objects with .embedding attribute)
            embeddings = []
            for result in response.results:
                # Each result.embeddings is already a list of embedding arrays
                embeddings.extend(result.embeddings)
            return array(embeddings)

        except Exception as e:
            raise ServiceResponseException(f"VoyageAI contextualized embedding request failed: {e}") from e

    @override
    async def generate_embeddings(
        self,
        texts: list[str],
        settings: "PromptExecutionSettings | None" = None,
        **kwargs: Any,
    ) -> ndarray:
        """Generate embeddings (wraps texts as single input for contextualized embeddings).

        Args:
            texts: List of texts to generate embeddings for.
            settings: Prompt execution settings (optional).
            kwargs: Additional arguments.

        Returns:
            ndarray: Array of embeddings.
        """
        return await self.generate_contextualized_embeddings([texts], settings, **kwargs)

    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        """Get the prompt execution settings class."""
        return VoyageAIContextualizedEmbeddingPromptExecutionSettings
