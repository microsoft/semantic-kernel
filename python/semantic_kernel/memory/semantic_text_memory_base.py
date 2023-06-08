# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from typing import List, Optional

from semantic_kernel.memory.memory_query_result import MemoryQueryResult


class SemanticTextMemoryBase(ABC):
    @abstractmethod
    async def save_information_async(
        self,
        collection: str,
        text: str,
        id: str,
        description: Optional[str] = None,
        additional_metadata: Optional[str] = None,
        # TODO: ctoken?
    ) -> None:
        pass

    @abstractmethod
    async def save_reference_async(
        self,
        collection: str,
        text: str,
        external_id: str,
        external_source_name: str,
        description: Optional[str] = None,
        additional_metadata: Optional[str] = None,
    ) -> None:
        pass

    @abstractmethod
    async def get_async(
        self,
        collection: str,
        query: str,
    ) -> Optional[MemoryQueryResult]:
        pass

    @abstractmethod
    async def search_async(
        self,
        collection: str,
        query: str,
        limit: int = 1,
        min_relevance_score: float = 0.7,
        # TODO: ctoken?
    ) -> List[MemoryQueryResult]:
        pass

    @abstractmethod
    async def get_collections_async(self) -> List[str]:
        pass
