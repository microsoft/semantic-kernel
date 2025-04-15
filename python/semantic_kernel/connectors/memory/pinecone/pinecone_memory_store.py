# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import NamedTuple

from numpy import ndarray
from pinecone import FetchResponse, IndexList, IndexModel, Pinecone, ServerlessSpec
from pydantic import ValidationError

from semantic_kernel.connectors.memory.pinecone.pinecone_settings import PineconeSettings
from semantic_kernel.connectors.memory.pinecone.utils import build_payload, parse_payload
from semantic_kernel.exceptions import (
    ServiceInitializationError,
    ServiceInvalidRequestError,
    ServiceResourceNotFoundError,
    ServiceResponseException,
)
from semantic_kernel.exceptions.memory_connector_exceptions import MemoryConnectorInitializationError
from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.utils.feature_stage_decorator import experimental

# Limitations set by Pinecone at https://docs.pinecone.io/reference/known-limitations
MAX_DIMENSIONALITY = 20000
MAX_UPSERT_BATCH_SIZE = 100
MAX_QUERY_WITHOUT_METADATA_BATCH_SIZE = 10000
MAX_QUERY_WITH_METADATA_BATCH_SIZE = 1000
MAX_FETCH_BATCH_SIZE = 1000
MAX_DELETE_BATCH_SIZE = 1000

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class PineconeMemoryStore(MemoryStoreBase):
    """A memory store that uses Pinecone as the backend."""

    _default_dimensionality: int

    DEFAULT_INDEX_SPEC: ServerlessSpec = ServerlessSpec(
        cloud="aws",
        region="us-east-1",
    )

    def __init__(
        self,
        api_key: str,
        default_dimensionality: int,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initializes a new instance of the PineconeMemoryStore class.

        Args:
            api_key (str): The Pinecone API key.
            default_dimensionality (int): The default dimensionality to use for new collections.
            env_file_path (str | None): Use the environment settings file as a fallback
                to environment variables. (Optional)
            env_file_encoding (str | None): The encoding of the environment settings file. (Optional)
        """
        if default_dimensionality > MAX_DIMENSIONALITY:
            raise MemoryConnectorInitializationError(
                f"Dimensionality of {default_dimensionality} exceeds the maximum allowed value of {MAX_DIMENSIONALITY}."
            )
        try:
            pinecone_settings = PineconeSettings(
                api_key=api_key,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise MemoryConnectorInitializationError("Failed to create Pinecone settings.", ex) from ex

        self._default_dimensionality = default_dimensionality

        self.pinecone = Pinecone(api_key=pinecone_settings.api_key.get_secret_value())
        self.collection_names_cache = set()

    async def create_collection(
        self,
        collection_name: str,
        dimension_num: int | None = None,
        distance_type: str | None = "cosine",
        index_spec: NamedTuple = DEFAULT_INDEX_SPEC,
    ) -> None:
        """Creates a new collection in Pinecone if it does not exist.

        This function creates an index, by default the following index
        settings are used: metric = cosine, cloud = aws, region = us-east-1.

        Args:
            collection_name (str): The name of the collection to create.
                In Pinecone, a collection is represented as an index. The concept
                of "collection" in Pinecone is just a static copy of an index.
            dimension_num (int, optional): The dimensionality of the embeddings.
            distance_type (str, optional): The distance metric to use for the index.
                (default: {"cosine"})
            index_spec (NamedTuple, optional): The index spec to use for the index.
        """
        if dimension_num is None:
            dimension_num = self._default_dimensionality
        if dimension_num > MAX_DIMENSIONALITY:
            raise ServiceInitializationError(
                f"Dimensionality of {dimension_num} exceeds " + f"the maximum allowed value of {MAX_DIMENSIONALITY}."
            )

        if not await self.does_collection_exist(collection_name):
            self.pinecone.create_index(
                name=collection_name, dimension=dimension_num, metric=distance_type, spec=index_spec
            )
            self.collection_names_cache.add(collection_name)

    async def describe_collection(self, collection_name: str) -> IndexModel | None:
        """Gets the description of the index.

        Args:
            collection_name (str): The name of the index to get.

        Returns:
            Optional[dict]: The index.
        """
        if await self.does_collection_exist(collection_name):
            return self.pinecone.describe_index(collection_name)
        return None

    async def get_collections(
        self,
    ) -> IndexList:
        """Gets the list of collections.

        Returns:
            IndexList: The list of collections.
        """
        return self.pinecone.list_indexes()

    async def delete_collection(self, collection_name: str) -> None:
        """Deletes a collection.

        Args:
            collection_name (str): The name of the collection to delete.

        Returns:
            None
        """
        if await self.does_collection_exist(collection_name):
            self.pinecone.delete_index(collection_name)
            self.collection_names_cache.discard(collection_name)

    async def does_collection_exist(self, collection_name: str) -> bool:
        """Checks if a collection exists.

        Args:
            collection_name (str): The name of the collection to check.

        Returns:
            bool: True if the collection exists; otherwise, False.
        """
        if collection_name in self.collection_names_cache:
            return True

        index_collection_names = self.pinecone.list_indexes().names()
        self.collection_names_cache |= set(index_collection_names)

        return collection_name in index_collection_names

    async def upsert(self, collection_name: str, record: MemoryRecord) -> str:
        """Upsert a record.

        Args:
            collection_name (str): The name of the collection to upsert the record into.
            record (MemoryRecord): The record to upsert.

        Returns:
            str: The unique database key of the record. In Pinecone, this is the record ID.
        """
        if not await self.does_collection_exist(collection_name):
            raise ServiceResourceNotFoundError(f"Collection '{collection_name}' does not exist")

        collection = self.pinecone.Index(collection_name)

        upsert_response = collection.upsert(
            vectors=[(record._id, record.embedding.tolist(), build_payload(record))],
            namespace="",
        )

        if upsert_response.upserted_count is None:
            raise ServiceResponseException(f"Error upserting record: {upsert_response.message}")

        return record._id

    async def upsert_batch(self, collection_name: str, records: list[MemoryRecord]) -> list[str]:
        """Upsert a batch of records.

        Args:
            collection_name (str): The name of the collection to upsert the records into.
            records (List[MemoryRecord]): The records to upsert.

        Returns:
            List[str]: The unique database keys of the records.
        """
        if not await self.does_collection_exist(collection_name):
            raise ServiceResourceNotFoundError(f"Collection '{collection_name}' does not exist")

        collection = self.pinecone.Index(collection_name)

        vectors = [
            (
                record._id,
                record.embedding.tolist(),
                build_payload(record),
            )
            for record in records
        ]

        upsert_response = collection.upsert(vectors, namespace="", batch_size=MAX_UPSERT_BATCH_SIZE)

        if upsert_response.upserted_count is None:
            raise ServiceResponseException(f"Error upserting record: {upsert_response.message}")
        return [record._id for record in records]

    async def get(self, collection_name: str, key: str, with_embedding: bool = False) -> MemoryRecord:
        """Gets a record.

        Args:
            collection_name (str): The name of the collection to get the record from.
            key (str): The unique database key of the record.
            with_embedding (bool): Whether to include the embedding in the result. (default: {False})

        Returns:
            MemoryRecord: The record.
        """
        if not await self.does_collection_exist(collection_name):
            raise ServiceResourceNotFoundError(f"Collection '{collection_name}' does not exist")

        collection = self.pinecone.Index(collection_name)
        fetch_response = collection.fetch([key])

        if len(fetch_response.vectors) == 0:
            raise ServiceResourceNotFoundError(f"Record with key '{key}' does not exist")

        return parse_payload(fetch_response.vectors[key], with_embedding)

    async def get_batch(
        self, collection_name: str, keys: list[str], with_embeddings: bool = False
    ) -> list[MemoryRecord]:
        """Gets a batch of records.

        Args:
            collection_name (str): The name of the collection to get the records from.
            keys (List[str]): The unique database keys of the records.
            with_embeddings (bool): Whether to include the embeddings in the results. (default: {False})

        Returns:
            List[MemoryRecord]: The records.
        """
        if not await self.does_collection_exist(collection_name):
            raise ServiceResourceNotFoundError(f"Collection '{collection_name}' does not exist")

        fetch_response = await self.__get_batch(collection_name, keys, with_embeddings)
        return [parse_payload(fetch_response.vectors[key], with_embeddings) for key in fetch_response.vectors]

    async def remove(self, collection_name: str, key: str) -> None:
        """Removes a record.

        Args:
            collection_name (str): The name of the collection to remove the record from.
            key (str): The unique database key of the record to remove.

        Returns:
            None
        """
        if not await self.does_collection_exist(collection_name):
            raise ServiceResourceNotFoundError(f"Collection '{collection_name}' does not exist")

        collection = self.pinecone.Index(collection_name)
        collection.delete([key])

    async def remove_batch(self, collection_name: str, keys: list[str]) -> None:
        """Removes a batch of records.

        Args:
            collection_name (str): The name of the collection to remove the records from.
            keys (List[str]): The unique database keys of the records to remove.

        Returns:
            None
        """
        if not await self.does_collection_exist(collection_name):
            raise ServiceResourceNotFoundError(f"Collection '{collection_name}' does not exist")

        collection = self.pinecone.Index(collection_name)
        for i in range(0, len(keys), MAX_DELETE_BATCH_SIZE):
            collection.delete(keys[i : i + MAX_DELETE_BATCH_SIZE])
        collection.delete(keys)

    async def get_nearest_match(
        self,
        collection_name: str,
        embedding: ndarray,
        min_relevance_score: float = 0.0,
        with_embedding: bool = False,
    ) -> tuple[MemoryRecord, float]:
        """Gets the nearest match to an embedding using cosine similarity.

        Args:
            collection_name (str): The name of the collection to get the nearest match from.
            embedding (ndarray): The embedding to find the nearest match to.
            min_relevance_score (float): The minimum relevance score of the match. (default: {0.0})
            with_embedding (bool): Whether to include the embedding in the result. (default: {False})

        Returns:
            Tuple[MemoryRecord, float]: The record and the relevance score.
        """
        matches = await self.get_nearest_matches(
            collection_name=collection_name,
            embedding=embedding,
            limit=1,
            min_relevance_score=min_relevance_score,
            with_embeddings=with_embedding,
        )
        return matches[0]

    async def get_nearest_matches(
        self,
        collection_name: str,
        embedding: ndarray,
        limit: int,
        min_relevance_score: float = 0.0,
        with_embeddings: bool = False,
    ) -> list[tuple[MemoryRecord, float]]:
        """Gets the nearest matches to an embedding using cosine similarity.

        Args:
            collection_name (str): The name of the collection to get the nearest matches from.
            embedding (ndarray): The embedding to find the nearest matches to.
            limit (int): The maximum number of matches to return.
            min_relevance_score (float): The minimum relevance score of the matches. (default: {0.0})
            with_embeddings (bool): Whether to include the embeddings in the results. (default: {False})

        Returns:
            List[Tuple[MemoryRecord, float]]: The records and their relevance scores.
        """
        if not await self.does_collection_exist(collection_name):
            raise ServiceResourceNotFoundError(f"Collection '{collection_name}' does not exist")

        collection = self.pinecone.Index(collection_name)

        if limit > MAX_QUERY_WITHOUT_METADATA_BATCH_SIZE:
            raise ServiceInvalidRequestError(
                "Limit must be less than or equal to " + f"{MAX_QUERY_WITHOUT_METADATA_BATCH_SIZE}"
            )
        if limit > MAX_QUERY_WITH_METADATA_BATCH_SIZE:
            query_response = collection.query(
                vector=embedding.tolist(),
                top_k=limit,
                include_values=False,
                include_metadata=False,
            )
            keys = [match.id for match in query_response.matches]
            fetch_response = await self.__get_batch(collection_name, keys, with_embeddings)
            vectors = fetch_response.vectors
            for match in query_response.matches:
                vectors[match.id].update(match)
            matches = [vectors[key] for key in vectors]
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

    async def __get_batch(
        self, collection_name: str, keys: list[str], with_embeddings: bool = False
    ) -> "FetchResponse":
        index = self.pinecone.Index(collection_name)
        if len(keys) > MAX_FETCH_BATCH_SIZE:
            fetch_response = index.fetch(keys[0:MAX_FETCH_BATCH_SIZE])
            for i in range(MAX_FETCH_BATCH_SIZE, len(keys), MAX_FETCH_BATCH_SIZE):
                fetch_response.vectors.update(index.fetch(keys[i : i + MAX_FETCH_BATCH_SIZE]).vectors)
        else:
            fetch_response = index.fetch(keys)
        return fetch_response
