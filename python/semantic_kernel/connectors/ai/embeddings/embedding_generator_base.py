# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from semantic_kernel.services.ai_service_client_base import AIServiceClientBase
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from numpy import ndarray

    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


@experimental
class EmbeddingGeneratorBase(AIServiceClientBase, ABC):
    """Base class for embedding generators."""

    @abstractmethod
    async def generate_embeddings(
        self,
        texts: list[str],
        settings: "PromptExecutionSettings | None" = None,
        **kwargs: Any,
    ) -> "ndarray":
        """Returns embeddings for the given texts as ndarray.

        Args:
            texts (List[str]): The texts to generate embeddings for.
            settings (PromptExecutionSettings): The settings to use for the request, optional.
            kwargs (Any): Additional arguments to pass to the request.
        """
        pass

    async def generate_raw_embeddings(
        self,
        texts: list[str],
        settings: "PromptExecutionSettings | None" = None,
        **kwargs: Any,
    ) -> Any:
        """Returns embeddings for the given texts in the unedited format.

        This is not implemented for all embedding services, falling back to the generate_embeddings method.

        Args:
            texts (List[str]): The texts to generate embeddings for.
            settings (PromptExecutionSettings): The settings to use for the request, optional.
            kwargs (Any): Additional arguments to pass to the request.
        """
        return await self.generate_embeddings(texts, settings, **kwargs)
