# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import List, Optional, Tuple

import pinecone
from numpy import ndarray
from pinecone import FetchResponse, IndexDescription

from semantic_kernel.connectors.memory.pinecone.utils import (
    build_payload,
    parse_payload,
)
from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.utils.null_logger import NullLogger

# Limitations set by Pinecone at https://docs.pinecone.io/docs/limits
MAX_DIMENSIONALITY = 20000
MAX_UPSERT_BATCH_SIZE = 100
MAX_QUERY_WITHOUT_METADATA_BATCH_SIZE = 10000
MAX_QUERY_WITH_METADATA_BATCH_SIZE = 1000
MAX_FETCH_BATCH_SIZE = 1000
MAX_DELETE_BATCH_SIZE = 1000


class PineconeMemoryStore(MemoryStoreBase):
    """A memory store that uses Pinecone as the backend."""

    _logger: Logger
    _pinecone_api_key: str
    _pinecone_environment: str
    _default_dimensionality: int

    def __init__(
        self,
        api_key: str,
        environment: str,
        default_dimensionality: int,
        logger: Optional[Logger] = None,
    ) -> None:
        """Initializes a new instance of the PineconeMemoryStore class.

        Arguments:
            pinecone_api_key {str} -- The Pinecone API key.
            pinecone_environment {str} -- The Pinecone environment.
            default_dimensionality {int} -- The default dimensionality to use for new collections.
            logger {Optional[Logger]} -- The logger to use. (default: {None})
        """
        if default_dimensionality > MAX_DIMENSIONALITY:
            raise ValueError(
                f"Dimensionality of {default_dimensionality} exceeds "
                + f"the maximum allowed value of {MAX_DIMENSIONALITY}."
            )
        self._pinecone_api_key = api_key
        self._pinecone_environment = environment
        self._default_dimensionality = default_dimensionality
        self._logger = logger or NullLogger()

        pinecone.init(
            api_key=self._pinecone_api_key, environment=self._pinecone_environment
        )

    def get_collections(self) -> List[str]:
        return pinecone.list_indexes()

    async def create_collection_async(
        self,
        collection_name: str,
        dimension_num: Optional[int] = None,
        distance_type: Optional[str] = "cosine",
        num_of_pods: Optional[int] = 1,
        replica_num: Optional[int] = 0,
        type_of_pod: Optional[str] = "p1.x1",
        metadata_config: Optional[dict] = None,
    ) -> None:
        """Creates a new collection in Pinecone if it does not exist.
            This function creates an index, by default the following index
            settings are used: metric = cosine, pods = 1, replicas = 0,
            pod_type = p1.x1, metadata_config = None.

        Arguments:
            collection_name {str} -- The name of the collection to create.
            In Pinecone, a collection is represented as an index. The concept
            of "collection" in Pinecone is just a static copy of an index.

        Returns:
            None
        """
        if dimension_num is None:
            dimension_num = self._default_dimensionality
        if dimension_num > MAX_DIMENSIONALITY:
            raise ValueError(
                f"Dimensionality of {dimension_num} exceeds "
                + f"the maximum allowed value of {MAX_DIMENSIONALITY}."
            )

        if collection_name not in pinecone.list_indexes():
            pinecone.create_index(
                name=collection_name,
                dimension=dimension_num,
                metric=distance_type,
                pods=num_of_pods,
                replicas=replica_num,
                pod_type=type_of_pod,
                metadata_config=metadata_config,
            )

    async def describe_collection_async(
        self, collection_name: str
    ) -> Optional[IndexDescription]:
        """Gets the description of the index.
        Arguments:
            collection_name {str} -- The name of the index to get.
        Returns:
            Optional[dict] -- The index.
        """
        if collection_name in pinecone.list_indexes():
            return pinecone.describe_index(collection_name)
        return None

    async def get_collections_async(
        self,
    ) -> List[str]:
        """Gets the list of collections.

        Returns:
            List[str] -- The list of collections.
        """
        return list(pinecone.list_indexes())

    async def delete_collection_async(self, collection_name: str) -> None:
        """Deletes a collection.

        Arguments:
            collection_name {str} -- The name of the collection to delete.

        Returns:
            None
        """
        if collection_name in pinecone.list_indexes():
            pinecone.delete_index(collection_name)

    async def does_collection_exist_async(self, collection_name: str) -> bool:
        """Checks if a collection exists.

        Arguments:
            collection_name {str} -- The name of the collection to check.

        Returns:
            bool -- True if the collection exists; otherwise, False.
        """
        return collection_name in pinecone.list_indexes()

    async def upsert_async(self, collection_name: str, record: MemoryRecord) -> str:
        """Upserts a record.

        Arguments:
            collection_name {str} -- The name of the collection to upsert the record into.
            record {MemoryRecord} -- The record to upsert.

        Returns:
            str -- The unique database key of the record. In Pinecone, this is the record ID.
        """
        if collection_name not in pinecone.list_indexes():
            raise Exception(f"Collection '{collection_name}' does not exist")

        collection = pinecone.Index(collection_name)

        upsert_response = collection.upsert(
            vectors=[(record._id, record.embedding.tolist(), build_payload(record))],
            namespace="",
        )

        if upsert_response.upserted_count is None:
            raise Exception(f"Error upserting record: {upsert_response.message}")

        return record._id

    async def upsert_batch_async(
        self, collection_name: str, records: List[MemoryRecord]
    ) -> List[str]:
        """Upserts a batch of records.

        Arguments:
            collection_name {str} -- The name of the collection to upsert the records into.
            records {List[MemoryRecord]} -- The records to upsert.

        Returns:
            List[str] -- The unique database keys of the records.
        """
        if collection_name not in pinecone.list_indexes():
            raise Exception(f"Collection '{collection_name}' does not exist")

        collection = pinecone.Index(collection_name)

        vectors = [
            (
                record._id,
                record.embedding.tolist(),
                build_payload(record),
            )
            for record in records
        ]

        upsert_response = collection.upsert(
            vectors, namespace="", batch_size=MAX_UPSERT_BATCH_SIZE
        )

        if upsert_response.upserted_count is None:
            raise Exception(f"Error upserting record: {upsert_response.message}")
        else:
            return [record._id for record in records]

    async def get_async(
        self, collection_name: str, key: str, with_embedding: bool = False
    ) -> MemoryRecord:
        """Gets a record.

        Arguments:
            collection_name {str} -- The name of the collection to get the record from.
            key {str} -- The unique database key of the record.
            with_embedding {bool} -- Whether to include the embedding in the result. (default: {False})

        Returns:
            MemoryRecord -- The record.
        """
        if collection_name not in pinecone.list_indexes():
            raise Exception(f"Collection '{collection_name}' does not exist")

        collection = pinecone.Index(collection_name)
        fetch_response = collection.fetch([key])

        if len(fetch_response.vectors) == 0:
            raise KeyError(f"Record with key '{key}' does not exist")

        return parse_payload(fetch_response.vectors[key], with_embedding)

    async def get_batch_async(
        self, collection_name: str, keys: List[str], with_embeddings: bool = False
    ) -> List[MemoryRecord]:
        """Gets a batch of records.

        Arguments:
            collection_name {str} -- The name of the collection to get the records from.
            keys {List[str]} -- The unique database keys of the records.
            with_embeddings {bool} -- Whether to include the embeddings in the results. (default: {False})

        Returns:
            List[MemoryRecord] -- The records.
        """
        if collection_name not in pinecone.list_indexes():
            raise Exception(f"Collection '{collection_name}' does not exist")

        fetch_response = await self.__get_batch_async(
            collection_name, keys, with_embeddings
        )
        return [
            parse_payload(fetch_response.vectors[key], with_embeddings)
            for key in fetch_response.vectors.keys()
        ]

    async def remove_async(self, collection_name: str, key: str) -> None:
        """Removes a record.

        Arguments:
            collection_name {str} -- The name of the collection to remove the record from.
            key {str} -- The unique database key of the record to remove.

        Returns:
            None
        """
        if collection_name not in pinecone.list_indexes():
            raise Exception(f"Collection '{collection_name}' does not exist")

        collection = pinecone.Index(collection_name)
        collection.delete([key])

    async def remove_batch_async(self, collection_name: str, keys: List[str]) -> None:
        """Removes a batch of records.

        Arguments:
            collection_name {str} -- The name of the collection to remove the records from.
            keys {List[str]} -- The unique database keys of the records to remove.

        Returns:
            None
        """
        if collection_name not in pinecone.list_indexes():
            raise Exception(f"Collection '{collection_name}' does not exist")

        collection = pinecone.Index(collection_name)
        for i in range(0, len(keys), MAX_DELETE_BATCH_SIZE):
            collection.delete(keys[i : i + MAX_DELETE_BATCH_SIZE])
        collection.delete(keys)

    async def get_nearest_match_async(
        self,
        collection_name: str,
        embedding: ndarray,
        min_relevance_score: float = 0.0,
        with_embedding: bool = False,
    ) -> Tuple[MemoryRecord, float]:
        """Gets the nearest match to an embedding using cosine similarity.

        Arguments:
            collection_name {str} -- The name of the collection to get the nearest match from.
            embedding {ndarray} -- The embedding to find the nearest match to.
            min_relevance_score {float} -- The minimum relevance score of the match. (default: {0.0})
            with_embedding {bool} -- Whether to include the embedding in the result. (default: {False})

        Returns:
            Tuple[MemoryRecord, float] -- The record and the relevance score.
        """
        matches = await self.get_nearest_matches_async(
            collection_name=collection_name,
            embedding=embedding,
            limit=1,
            min_relevance_score=min_relevance_score,
            with_embeddings=with_embedding,
        )
        return matches[0]

    async def get_nearest_matches_async(
        self,
        collection_name: str,
        embedding: ndarray,
        limit: int,
        min_relevance_score: float = 0.0,
        with_embeddings: bool = False,
    ) -> List[Tuple[MemoryRecord, float]]:
        """Gets the nearest matches to an embedding using cosine similarity.

        Arguments:
            collection_name {str} -- The name of the collection to get the nearest matches from.
            embedding {ndarray} -- The embedding to find the nearest matches to.
            limit {int} -- The maximum number of matches to return.
            min_relevance_score {float} -- The minimum relevance score of the matches. (default: {0.0})
            with_embeddings {bool} -- Whether to include the embeddings in the results. (default: {False})

        Returns:
            List[Tuple[MemoryRecord, float]] -- The records and their relevance scores.
        """
        if collection_name not in pinecone.list_indexes():
            raise Exception(f"Collection '{collection_name}' does not exist")

        collection = pinecone.Index(collection_name)

        if limit > MAX_QUERY_WITHOUT_METADATA_BATCH_SIZE:
            raise Exception(
                "Limit must be less than or equal to "
                + f"{MAX_QUERY_WITHOUT_METADATA_BATCH_SIZE}"
            )
        elif limit > MAX_QUERY_WITH_METADATA_BATCH_SIZE:
            query_response = collection.query(
                vector=embedding.tolist(),
                top_k=limit,
                include_values=False,
                include_metadata=False,
            )
            keys = [match.id for match in query_response.matches]
            fetch_response = await self.__get_batch_async(
                collection_name, keys, with_embeddings
            )
            vectors = fetch_response.vectors
            for match in query_response.matches:
                vectors[match.id].update(match)
            matches = [vectors[key] for key in vectors.keys()]
        else:
            query_response = collection.query(
                vector=embedding.tolist(),
                top_k=limit,
                include_values=with_embeddings,
                include_metadata=True,
            )
            matches = query_response.matches
        if min_relevance_score is not None:
            matches = [match for match in matches if match.score >= min_relevance_score]
        return (
            [
                (
                    parse_payload(match, with_embeddings),
                    match["score"],
                )
                for match in matches
            ]
            if len(matches) > 0
            else []
        )

    async def __get_batch_async(
        self, collection_name: str, keys: List[str], with_embeddings: bool = False
    ) -> "FetchResponse":
        index = pinecone.Index(collection_name)
        if len(keys) > MAX_FETCH_BATCH_SIZE:
            fetch_response = index.fetch(keys[0:MAX_FETCH_BATCH_SIZE])
            for i in range(MAX_FETCH_BATCH_SIZE, len(keys), MAX_FETCH_BATCH_SIZE):
                fetch_response.vectors.update(
                    index.fetch(keys[i : i + MAX_FETCH_BATCH_SIZE]).vectors
                )
        else:
            fetch_response = index.fetch(keys)
        return fetch_response
