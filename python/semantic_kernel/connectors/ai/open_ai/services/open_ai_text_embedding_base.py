# Copyright (c) Microsoft. All rights reserved.

from typing import List, Optional

from numpy import ndarray

from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import (
    EmbeddingGeneratorBase,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import (
    OpenAIHandler,
)


class OpenAITextEmbeddingBase(OpenAIHandler, EmbeddingGeneratorBase):
    async def generate_embeddings_async(
        self, texts: List[str], batch_size: Optional[int] = None
    ) -> ndarray:
        """Generates embeddings for the given texts.

        Arguments:
            texts {List[str]} -- The texts to generate embeddings for.
            batch_size {Optional[int]} -- The batch size to use for the request.

        Returns:
            ndarray -- The embeddings for the text.

        """
        return await self._send_embedding_request(texts, batch_size)
