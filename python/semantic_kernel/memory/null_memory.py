# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.memory.memory_query_result import MemoryQueryResult
from semantic_kernel.memory.semantic_text_memory_base import SemanticTextMemoryBase
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class NullMemory(SemanticTextMemoryBase):
    """Class for null memory."""

    async def save_information(
        self,
        collection: str,
        text: str,
        id: str,
        description: str | None = None,
        additional_metadata: str | None = None,
    ) -> None:
        """Nullifies behavior of SemanticTextMemoryBase save_information."""
        return

    async def save_reference(
        self,
        collection: str,
        text: str,
        external_id: str,
        external_source_name: str,
        description: str | None = None,
        additional_metadata: str | None = None,
    ) -> None:
        """Nullifies behavior of SemanticTextMemoryBase save_reference."""
        return

    async def get(self, collection: str, query: str) -> MemoryQueryResult | None:
        """Nullifies behavior of SemanticTextMemoryBase get."""
        return None

    async def search(
        self,
        collection: str,
        query: str,
        limit: int = 1,
        min_relevance_score: float = 0.7,
    ) -> list[MemoryQueryResult]:
        """Nullifies behavior of SemanticTextMemoryBase search."""
        return []

    async def get_collections(self) -> list[str]:
        """Nullifies behavior of SemanticTextMemoryBase get_collections."""
        return []


NullMemory.instance = NullMemory()  # type: ignore
