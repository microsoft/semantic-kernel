# Copyright (c) Microsoft. All rights reserved.

from typing import List, Optional

from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_query_result import MemoryQueryResult
from semantic_kernel.memory.storage.memory_storage_base import MemoryStorageBase
from semantic_kernel.ai.embeddings.embedding_generator_base import (
    EmbeddingGeneratorBase,
)
from semantic_kernel.memory.semantic_text_memory_base import SemanticTextMemoryBase


class SemanticTextMemory(SemanticTextMemoryBase):
    _storage: MemoryStorageBase
    _embeddings_generator: EmbeddingGeneratorBase

    def __init__(
        self, storage: MemoryStorageBase, embeddings_generator: EmbeddingGeneratorBase
    ) -> None:
        self._storage = storage
        self._embeddings_generator = embeddings_generator

    async def save_information_async(
        self,
        collection: str,
        text: str,
        id: str,
        description: Optional[str] = None,
        # TODO: ctoken?
    ) -> None:
        embedding = await self._embeddings_generator.generate_embeddings_async([text])
        data = MemoryRecord.local_record(id, text, description, embedding)

        await self._storage.put_value_async(collection, id, data)
