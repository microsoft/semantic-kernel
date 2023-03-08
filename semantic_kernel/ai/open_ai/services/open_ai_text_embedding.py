# Copyright (c) Microsoft. All rights reserved.

from typing import List

from numpy import ndarray

from semantic_kernel.ai.embeddings.embedding_generator_base import (
    EmbeddingGeneratorBase,
)


class OpenAITextEmbedding(EmbeddingGeneratorBase):
    async def generate_embeddings_async(self, texts: List[str]) -> ndarray:
        raise NotImplementedError()
