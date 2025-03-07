# Copyright (c) Microsoft. All rights reserved.

import sys
from typing import TYPE_CHECKING, Any

from numpy import array, ndarray

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIEmbeddingPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import OpenAIHandler
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


@experimental
class OpenAITextEmbeddingBase(OpenAIHandler, EmbeddingGeneratorBase):
    """Base class for OpenAI text embedding services."""

    @override
    async def generate_embeddings(
        self,
        texts: list[str],
        settings: "PromptExecutionSettings | None" = None,
        batch_size: int | None = None,
        **kwargs: Any,
    ) -> ndarray:
        raw_embeddings = await self.generate_raw_embeddings(texts, settings, batch_size, **kwargs)
        return array(raw_embeddings)

    @override
    async def generate_raw_embeddings(
        self,
        texts: list[str],
        settings: "PromptExecutionSettings | None" = None,
        batch_size: int | None = None,
        **kwargs: Any,
    ) -> Any:
        """Returns embeddings for the given texts in the unedited format.

        Args:
            texts (List[str]): The texts to generate embeddings for.
            settings (PromptExecutionSettings): The settings to use for the request.
            batch_size (int): The batch size to use for the request.
            kwargs (Dict[str, Any]): Additional arguments to pass to the request.
        """
        if not settings:
            settings = OpenAIEmbeddingPromptExecutionSettings(ai_model_id=self.ai_model_id)
        else:
            if not isinstance(settings, OpenAIEmbeddingPromptExecutionSettings):
                settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, OpenAIEmbeddingPromptExecutionSettings)  # nosec
        if settings.ai_model_id is None:
            settings.ai_model_id = self.ai_model_id
        for key, value in kwargs.items():
            setattr(settings, key, value)
        raw_embeddings = []
        batch_size = batch_size or len(texts)
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            settings.input = batch
            raw_embedding = await self._send_request(settings=settings)
            assert isinstance(raw_embedding, list)  # nosec
            raw_embeddings.extend(raw_embedding)
        return raw_embeddings

    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        """Get the request settings class."""
        return OpenAIEmbeddingPromptExecutionSettings
