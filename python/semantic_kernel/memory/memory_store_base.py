# Copyright (c) Microsoft. All rights reserved.

from abc import abstractmethod
from typing import List, Tuple

from numpy import ndarray

from semantic_kernel.memory.memory_record import MemoryRecord


class MemoryStoreBase:
    @abstractmethod
    async def create_collection_async(
        self,
        collection_name: str
        # TODO: cancel token
    ) -> None:
        pass

    @abstractmethod
    async def get_collections_async(
        self,
        # TODO: cancel token
    ) -> List[str]:
        pass

    @abstractmethod
    async def delete_collection_async(
        self,
        collection_name: str
        # TODO: cancel token
    ) -> None:
        pass

    @abstractmethod
    async def does_collection_exist_async(
        self,
        collection_name: str
        # TODO: cancel token
    ) -> bool:
        pass

    @abstractmethod
    async def upsert_async(
        self,
        collection_name: str,
        record: MemoryRecord
        # TODO: cancel token
    ) -> str:
        pass

    @abstractmethod
    async def upsert_batch_async(
        self,
        collection_name: str,
        records: List[MemoryRecord]
        # TODO: cancel token
    ) -> List[str]:
        pass

    @abstractmethod
    async def get_async(
        self,
        collection_name: str,
        key: str,
        with_embedding: bool
        # TODO: cancel token
    ) -> MemoryRecord:
        pass

    @abstractmethod
    async def get_batch_async(
        self,
        collection_name: str,
        keys: List[str],
        with_embeddings: bool
        # TODO: cancel token
    ) -> List[MemoryRecord]:
        pass

    @abstractmethod
    async def remove_async(
        self,
        collection_name: str,
        key: str
        # TODO: cancel token
    ) -> None:
        pass

    @abstractmethod
    async def remove_batch_async(
        self,
        collection_name: str,
        keys: List[str]
        # TODO: cancel token
    ) -> None:
        pass

    @abstractmethod
    async def get_nearest_matches_async(
        self,
        collection_name: str,
        embedding: ndarray,
        limit: int,
        min_relevance_score: float,
        with_embeddings: bool
        # TODO: cancel token
    ) -> List[Tuple[MemoryRecord, float]]:
        pass

    @abstractmethod
    async def get_nearest_match_async(
        self,
        collection_name: str,
        embedding: ndarray,
        min_relevance_score: float,
        with_embedding: bool
        # TODO: cancel token
    ) -> Tuple[MemoryRecord, float]:
        pass
