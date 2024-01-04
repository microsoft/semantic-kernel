# Copyright (c) Microsoft. All rights reserved.

from typing import Any, Dict, List, Optional

from numpy import array, ndarray

from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import (
    EmbeddingGeneratorBase,
)
from semantic_kernel.connectors.ai.open_ai.request_settings.open_ai_request_settings import (
    OpenAIEmbeddingRequestSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import (
    OpenAIHandler,
)


class OpenAITextEmbeddingBase(OpenAIHandler, EmbeddingGeneratorBase):
    async def generate_embeddings_async(
        self, texts: List[str], batch_size: Optional[int] = None, **kwargs: Dict[str, Any]
    ) -> ndarray:
        """Generates embeddings for the given texts.

        Arguments:
            texts {List[str]} -- The texts to generate embeddings for.
            batch_size {Optional[int]} -- The batch size to use for the request.
            kwargs {Dict[str, Any]} -- Additional arguments to pass to the request,
                see OpenAIEmbeddingRequestSettings for the details.

        Returns:
            ndarray -- The embeddings for the text.

        """
        settings = OpenAIEmbeddingRequestSettings(
            ai_model_id=self.ai_model_id,
            **kwargs,
        )
        raw_embeddings = []
        batch_size = batch_size or len(texts)
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]  # noqa: E203
            settings.input = batch
            raw_embedding = await self._send_embedding_request(
                settings=settings,
            )
            raw_embeddings.extend(raw_embedding)
        return array(raw_embeddings)

    def get_request_settings_class(self) -> AIRequestSettings:
        return OpenAIEmbeddingRequestSettings
