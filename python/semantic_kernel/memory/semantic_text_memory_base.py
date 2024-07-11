# Copyright (c) Microsoft. All rights reserved.

from abc import abstractmethod
from typing import List, Optional, TypeVar

from semantic_kernel.memory.memory_query_result import MemoryQueryResult
from semantic_kernel.sk_pydantic import PydanticField

SemanticTextMemoryT = TypeVar("SemanticTextMemoryT", bound="SemanticTextMemoryBase")


class SemanticTextMemoryBase(PydanticField):
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
        """Save information to the memory (calls the memory store's upsert method).

        Arguments:
            collection {str} -- The collection to save the information to.
            text {str} -- The text to save.
            id {str} -- The id of the information.
            description {Optional[str]} -- The description of the information.

        Returns:
            None -- None.
        """
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
        """Save a reference to the memory (calls the memory store's upsert method).

        Arguments:
            collection {str} -- The collection to save the reference to.
            text {str} -- The text to save.
            external_id {str} -- The external id of the reference.
            external_source_name {str} -- The external source name of the reference.
            description {Optional[str]} -- The description of the reference.

        Returns:
            None -- None.
        """
        pass

    @abstractmethod
    async def get_async(
        self,
        collection: str,
        query: str,
        # TODO: with_embedding: bool,
    ) -> Optional[MemoryQueryResult]:
        """Get information from the memory (calls the memory store's get method).

        Arguments:
            collection {str} -- The collection to get the information from.
            key {str} -- The key of the information.

        Returns:
            Optional[MemoryQueryResult] -- The MemoryQueryResult if found, None otherwise.
        """
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
        """Search the memory (calls the memory store's get_nearest_matches method).

        Arguments:
            collection {str} -- The collection to search in.
            query {str} -- The query to search for.
            limit {int} -- The maximum number of results to return. (default: {1})
            min_relevance_score {float} -- The minimum relevance score to return. (default: {0.0})
            with_embeddings {bool} -- Whether to return the embeddings of the results. (default: {False})

        Returns:
            List[MemoryQueryResult] -- The list of MemoryQueryResult found.
        """
        pass

    @abstractmethod
    async def get_collections_async(self) -> List[str]:
        """Get the list of collections in the memory (calls the memory store's get_collections method).

        Returns:
            List[str] -- The list of all the memory collection names.
        """
        pass
