# Copyright (c) Microsoft. All rights reserved.

from typing import List, Optional

from semantic_kernel.memory.memory_query_result import MemoryQueryResult
from semantic_kernel.memory.semantic_text_memory_base import SemanticTextMemoryBase


class NullMemory(SemanticTextMemoryBase):
    async def save_information_async(
        self,
        collection: str,
        text: str,
        id: str,
        description: Optional[str] = None,
        additional_metadata: Optional[str] = None,
    ) -> None:
        """Nullifies behavior of SemanticTextMemoryBase.save_information_async()"""
        return None

    async def save_reference_async(
        self,
        collection: str,
        text: str,
        external_id: str,
        external_source_name: str,
        description: Optional[str] = None,
        additional_metadata: Optional[str] = None,
    ) -> None:
        """Nullifies behavior of SemanticTextMemoryBase.save_reference_async()"""
        return None

    async def get_async(
        self, collection: str, query: str
    ) -> Optional[MemoryQueryResult]:
        """Nullifies behavior of SemanticTextMemoryBase.get_async()"""
        return None

    async def search_async(
        self,
        collection: str,
        query: str,
        limit: int = 1,
        min_relevance_score: float = 0.7,
    ) -> List[MemoryQueryResult]:
        """Nullifies behavior of SemanticTextMemoryBase.search_async()"""
        return []

    async def get_collections_async(self) -> List[str]:
        """Nullifies behavior of SemanticTextMemoryBase.get_collections_async()"""
        return []


NullMemory.instance = NullMemory()  # type: ignore
