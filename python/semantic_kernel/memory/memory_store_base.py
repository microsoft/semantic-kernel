# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod

from numpy import ndarray

from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class MemoryStoreBase(ABC):
    """Base class for memory store."""

    async def __aenter__(self):
        """Enter the context manager."""
        return self

    async def __aexit__(self, *args):
        """Exit the context manager."""
        await self.close()

    async def close(self):
        """Close the connection."""
        pass

    @abstractmethod
    async def create_collection(self, collection_name: str) -> None:
        """Creates a new collection in the data store.

        Args:
            collection_name (str): The name associated with a collection of embeddings.
        """
        pass

    @abstractmethod
    async def get_collections(
        self,
    ) -> list[str]:
        """Gets all collection names in the data store.

        Returns:
            List[str]: A group of collection names.
        """
        pass

    @abstractmethod
    async def delete_collection(self, collection_name: str) -> None:
        """Deletes a collection from the data store.

        Args:
            collection_name (str): The name associated with a collection of embeddings.
        """
        pass

    @abstractmethod
    async def does_collection_exist(self, collection_name: str) -> bool:
        """Determines if a collection exists in the data store.

        Args:
            collection_name (str): The name associated with a collection of embeddings.

        Returns:
            bool: True if given collection exists, False if not.
        """
        pass

    @abstractmethod
    async def upsert(self, collection_name: str, record: MemoryRecord) -> str:
        """Upserts a memory record into the data store.

        Does not guarantee that the collection exists.
        If the record already exists, it will be updated.
        If the record does not exist, it will be created.

        Args:
            collection_name (str): The name associated with a collection of embeddings.
            record (MemoryRecord): The memory record to upsert.

        Returns:
            str: The unique identifier for the memory record.
        """
        pass

    @abstractmethod
    async def upsert_batch(self, collection_name: str, records: list[MemoryRecord]) -> list[str]:
        """Upserts a group of memory records into the data store.

        Does not guarantee that the collection exists.
        If the record already exists, it will be updated.
        If the record does not exist, it will be created.

        Args:
            collection_name (str): The name associated with a collection of embeddings.
            records (MemoryRecord): The memory records to upsert.

        Returns:
            List[str]: The unique identifiers for the memory records.
        """
        pass

    @abstractmethod
    async def get(self, collection_name: str, key: str, with_embedding: bool) -> MemoryRecord:
        """Gets a memory record from the data store. Does not guarantee that the collection exists.

        Args:
            collection_name (str): The name associated with a collection of embeddings.
            key (str): The unique id associated with the memory record to get.
            with_embedding (bool): If true, the embedding will be returned in the memory record.

        Returns:
            MemoryRecord: The memory record if found
        """
        pass

    @abstractmethod
    async def get_batch(
        self,
        collection_name: str,
        keys: list[str],
        with_embeddings: bool,
    ) -> list[MemoryRecord]:
        """Gets a batch of memory records from the data store. Does not guarantee that the collection exists.

        Args:
            collection_name (str): The name associated with a collection of embeddings.
            keys (List[str]): The unique ids associated with the memory records to get.
            with_embeddings (bool): If true, the embedding will be returned in the memory records.

        Returns:
            List[MemoryRecord]: The memory records associated with the unique keys provided.
        """
        pass

    @abstractmethod
    async def remove(self, collection_name: str, key: str) -> None:
        """Removes a memory record from the data store. Does not guarantee that the collection exists.

        Args:
            collection_name (str): The name associated with a collection of embeddings.
            key (str): The unique id associated with the memory record to remove.
        """
        pass

    @abstractmethod
    async def remove_batch(self, collection_name: str, keys: list[str]) -> None:
        """Removes a batch of memory records from the data store. Does not guarantee that the collection exists.

        Args:
            collection_name (str): The name associated with a collection of embeddings.
            keys (List[str]): The unique ids associated with the memory records to remove.
        """
        pass

    @abstractmethod
    async def get_nearest_matches(
        self,
        collection_name: str,
        embedding: ndarray,
        limit: int,
        min_relevance_score: float,
        with_embeddings: bool,
    ) -> list[tuple[MemoryRecord, float]]:
        """Gets the nearest matches to an embedding of type float. Does not guarantee that the collection exists.

        Args:
            collection_name (str): The name associated with a collection of embeddings.
            embedding (ndarray): The embedding to compare the collection's embeddings with.
            limit (int): The maximum number of similarity results to return.
            min_relevance_score (float): The minimum relevance threshold for returned results.
            with_embeddings (bool): If true, the embeddings will be returned in the memory records.

        Returns:
            List[Tuple[MemoryRecord, float]]: A list of tuples where item1 is a MemoryRecord and item2
                is its similarity score as a float.
        """
        pass

    @abstractmethod
    async def get_nearest_match(
        self,
        collection_name: str,
        embedding: ndarray,
        min_relevance_score: float,
        with_embedding: bool,
    ) -> tuple[MemoryRecord, float]:
        """Gets the nearest match to an embedding of type float. Does not guarantee that the collection exists.

        Args:
            collection_name (str): The name associated with a collection of embeddings.
            embedding (ndarray): The embedding to compare the collection's embeddings with.
            min_relevance_score (float): The minimum relevance threshold for returned result.
            with_embedding (bool): If true, the embeddings will be returned in the memory record.

        Returns:
            Tuple[MemoryRecord, float]: A tuple consisting of the MemoryRecord and the similarity score as a float.
        """
        pass
