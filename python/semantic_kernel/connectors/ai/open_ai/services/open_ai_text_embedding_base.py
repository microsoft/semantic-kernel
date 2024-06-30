# Copyright (c) Microsoft. All rights reserved.

import sys
from typing import Any

from numpy import array, ndarray

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIEmbeddingPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import OpenAIHandler
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class OpenAITextEmbeddingBase(OpenAIHandler, EmbeddingGeneratorBase):
    @override
    async def generate_embeddings(self, texts: list[str], batch_size: int | None = None, **kwargs: Any) -> ndarray:
        settings = OpenAIEmbeddingPromptExecutionSettings(
            ai_model_id=self.ai_model_id,
            **kwargs,
        )
        raw_embeddings = []
        batch_size = batch_size or len(texts)
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            settings.input = batch
            raw_embedding = await self._send_embedding_request(
                settings=settings,
            )
            raw_embeddings.extend(raw_embedding)
        return array(raw_embeddings)

    @override
    def get_prompt_execution_settings_class(self) -> PromptExecutionSettings:
        return OpenAIEmbeddingPromptExecutionSettings
