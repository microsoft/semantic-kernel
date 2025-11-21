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
    VoyageAIEmbeddingPromptExecutionSettings,
)
from semantic_kernel.exceptions.service_exceptions import ServiceResponseException

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


class VoyageAITextEmbedding(VoyageAIBase, EmbeddingGeneratorBase):
    """VoyageAI Text Embedding Service.

    Supports models like:
    - voyage-3-large
    - voyage-3.5
    - voyage-3.5-lite
    - voyage-code-3
    - voyage-finance-2
    - voyage-law-2
    """

    @override
    async def generate_embeddings(
        self,
        texts: list[str],
        settings: "PromptExecutionSettings | None" = None,
        **kwargs: Any,
    ) -> ndarray:
        """Generate embeddings for the given texts.

        Args:
            texts: List of texts to generate embeddings for (max 1,000 items).
            settings: Prompt execution settings (optional).
            kwargs: Additional arguments to pass to the request.

        Returns:
            ndarray: Array of embeddings.
        """
        if not settings:
            settings = VoyageAIEmbeddingPromptExecutionSettings()
        else:
            settings = self.get_prompt_execution_settings_from_settings(settings)

        try:
            # Call VoyageAI embeddings API
            response = await self.aclient.embed(
                texts=texts,
                model=self.ai_model_id,
                **settings.prepare_settings_dict(),
            )

            # Extract embeddings
            embeddings = response.embeddings
            return array(embeddings)

        except Exception as e:
            raise ServiceResponseException(f"VoyageAI text embedding request failed: {e}") from e

    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        """Get the prompt execution settings class."""
        return VoyageAIEmbeddingPromptExecutionSettings
