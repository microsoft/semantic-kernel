# Copyright (c) Microsoft. All rights reserved.

from typing import List, Optional

from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import (
    EmbeddingGeneratorBase,
)
from semantic_kernel.memory.memory_query_result import MemoryQueryResult
from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.memory.semantic_text_memory_base import SemanticTextMemoryBase


class SemanticTextMemory(SemanticTextMemoryBase):
    _storage: MemoryStoreBase
    _embeddings_generator: EmbeddingGeneratorBase

    def __init__(
        self, storage: MemoryStoreBase, embeddings_generator: EmbeddingGeneratorBase
    ) -> None:
        self._storage = storage
        self._embeddings_generator = embeddings_generator

    async def save_information_async(
        self,
        collection: str,
        text: str,
        id: str,
        description: Optional[str] = None,
    ) -> None:
        
        #TODO: not the best place to create collection, but will address this behavior together with .NET SK
        if not await self._storage.does_collection_exist_async(collection_name=collection):
            await self._storage.create_collection_async(collection_name=collection)

        embedding = await self._embeddings_generator.generate_embeddings_async([text])
        data = MemoryRecord.local_record(id=id, text=text, description=description, embedding=embedding)

        await self._storage.upsert_async(collection_name=collection, record=data)

    async def save_reference_async(
        self,
        collection: str,
        text: str,
        external_id: str,
        external_source_name: str,
        description: Optional[str] = None,
    ) -> None:
        
        #TODO: not the best place to create collection, but will address this behavior together with .NET SK
        if not await self._storage.does_collection_exist_async(collection_name=collection):
            await self._storage.create_collection_async(collection_name=collection)

        embedding = await self._embeddings_generator.generate_embeddings_async([text])
        data = MemoryRecord.reference_record(
            id=external_id, source_name=external_source_name, description=description, embedding=embedding
        )

        await self._storage.upsert_async(collection_name=collection, record=data)

    async def get_async(
        self,
        collection: str,
        key: str,
    ) -> Optional[MemoryQueryResult]:
        record = await self._storage.get_async(collection_name=collection, key=key)
        return MemoryQueryResult.from_memory_record(record) if record else None

    async def search_async(
        self,
        collection: str,
        query: str,
        limit: int = 1,
        min_relevance_score: float = 0.7,
        with_embeddings: bool = False,
    ) -> List[MemoryQueryResult]:
        query_embedding = await self._embeddings_generator.generate_embeddings_async(
            [query]
        )
        results = await self._storage.get_nearest_matches_async(
            collection_name=collection,
            embedding=query_embedding, 
            limit=limit, 
            min_relevance_score=min_relevance_score,
            with_embeddings=with_embeddings
        )

        return [MemoryQueryResult.from_memory_record(r[0], r[1]) for r in results]

    async def get_collections_async(self) -> List[str]:
        return await self._storage.get_collections_async()
