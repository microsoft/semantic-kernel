# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from typing import List, Tuple

from numpy import ndarray

from semantic_kernel.memory.memory_record import MemoryRecord


class MemoryStoreBase(ABC):
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close_async()

    async def close_async(self):
        pass

    @abstractmethod
    async def create_collection_async(self, collection_name: str) -> None:
        pass

    @abstractmethod
    async def get_collections_async(
        self,
    ) -> List[str]:
        pass

    @abstractmethod
    async def delete_collection_async(self, collection_name: str) -> None:
        pass

    @abstractmethod
    async def does_collection_exist_async(self, collection_name: str) -> bool:
        pass

    @abstractmethod
    async def upsert_async(self, collection_name: str, record: MemoryRecord) -> str:
        pass

    @abstractmethod
    async def upsert_batch_async(
        self, collection_name: str, records: List[MemoryRecord]
    ) -> List[str]:
        pass

    @abstractmethod
    async def get_async(
        self, collection_name: str, key: str, with_embedding: bool
    ) -> MemoryRecord:
        pass

    @abstractmethod
    async def get_batch_async(
        self, collection_name: str, keys: List[str], with_embeddings: bool
    ) -> List[MemoryRecord]:
        pass

    @abstractmethod
    async def remove_async(self, collection_name: str, key: str) -> None:
        pass

    @abstractmethod
    async def remove_batch_async(self, collection_name: str, keys: List[str]) -> None:
        pass

    @abstractmethod
    async def get_nearest_matches_async(
        self,
        collection_name: str,
        embedding: ndarray,
        limit: int,
        min_relevance_score: float,
        with_embeddings: bool,
    ) -> List[Tuple[MemoryRecord, float]]:
        pass

    @abstractmethod
    async def get_nearest_match_async(
        self,
        collection_name: str,
        embedding: ndarray,
        min_relevance_score: float,
        with_embedding: bool,
    ) -> Tuple[MemoryRecord, float]:
        pass
