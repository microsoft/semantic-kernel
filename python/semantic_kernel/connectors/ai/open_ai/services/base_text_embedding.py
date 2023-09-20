# Copyright (c) Microsoft. All rights reserved.

from typing import List, Optional

from numpy import ndarray

from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import (
    EmbeddingGeneratorBase,
)
from semantic_kernel.connectors.ai.open_ai.services.base_open_ai_functions import (
    OpenAIServiceCalls,
)


class BaseTextEmbedding(OpenAIServiceCalls, EmbeddingGeneratorBase):
    async def generate_embeddings_async(
        self, texts: List[str], batch_size: Optional[int] = None
    ) -> ndarray:
        return await self._send_embedding_request(texts, batch_size)
