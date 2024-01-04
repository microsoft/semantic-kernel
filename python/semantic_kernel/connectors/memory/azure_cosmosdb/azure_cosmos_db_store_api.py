# Copyright (c) Microsoft. All rights reserved.


from abc import ABC, abstractmethod
from typing import List, Tuple

from numpy import ndarray

from semantic_kernel.memory.memory_record import MemoryRecord


# Abstract class similar to the original data store that allows API level abstraction
class AzureCosmosDBStoreApi(ABC):
    @abstractmethod
    async def create_collection(self, collection_name: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_collections(self) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    async def delete_collection(self, collection_name: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def does_collection_exist(self, collection_name: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def upsert(self, collection_name: str, record: MemoryRecord) -> str:
        raise NotImplementedError

    @abstractmethod
    async def upsert_batch(self, collection_name: str, records: List[MemoryRecord]) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    async def get(self, collection_name: str, key: str, with_embedding: bool) -> MemoryRecord:
        raise NotImplementedError

    @abstractmethod
    async def get_batch(self, collection_name: str, keys: List[str], with_embeddings: bool) -> List[MemoryRecord]:
        raise NotImplementedError

    @abstractmethod
    async def remove(self, collection_name: str, key: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def remove_batch(self, collection_name: str, keys: List[str]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_nearest_matches(
        self,
        collection_name: str,
        embedding: ndarray,
        limit: int,
        min_relevance_score: float,
        with_embeddings: bool,
    ) -> List[Tuple[MemoryRecord, float]]:
        raise NotImplementedError

    @abstractmethod
    async def get_nearest_match(
        self,
        collection_name: str,
        embedding: ndarray,
        min_relevance_score: float,
        with_embedding: bool,
    ) -> Tuple[MemoryRecord, float]:
        raise NotImplementedError
