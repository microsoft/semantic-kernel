# Copyright (c) Microsoft. All rights reserved.

import logging

import numpy as np
import redis
from numpy import ndarray
from pydantic import ValidationError
from redis.commands.search.field import TextField, VectorField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from redis.exceptions import ResponseError

from semantic_kernel.connectors.memory.redis.redis_settings import RedisSettings
from semantic_kernel.connectors.memory.redis.utils import (
    deserialize_document_to_record,
    deserialize_redis_to_record,
    get_redis_key,
    serialize_record_to_redis,
)
from semantic_kernel.exceptions import (
    ServiceResourceNotFoundError,
    ServiceResponseException,
)
from semantic_kernel.exceptions.memory_connector_exceptions import MemoryConnectorInitializationError
from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.utils.feature_stage_decorator import experimental

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class RedisMemoryStore(MemoryStoreBase):
    """A memory store implementation using Redis."""

    _database: "redis.Redis"
    _ft: "redis.Redis.ft"
    # Without RedisAI, it is currently not possible to retrieve index-specific vector attributes to have
    # fully independent collections.
    _query_dialect: int
    _vector_distance_metric: str
    _vector_index_algorithm: str
    _vector_size: int
    _vector_type: "np.dtype"
    _vector_type_str: str

    def __init__(
        self,
        connection_string: str,
        vector_size: int = 1536,
        vector_distance_metric: str = "COSINE",
        vector_type: str = "FLOAT32",
        vector_index_algorithm: str = "HNSW",
        query_dialect: int = 2,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """RedisMemoryStore is an abstracted interface to interact with a Redis node connection.

        See documentation about connections: https://redis-py.readthedocs.io/en/stable/connections.html
        See documentation about vector attributes: https://redis.io/docs/stack/search/reference/vectors.

        Args:
            connection_string (str): Provide connection URL to a Redis instance
            vector_size (str): Size of vectors, defaults to 1536
            vector_distance_metric (str): Metric for measuring vector distances, defaults to COSINE
            vector_type (str): Vector type, defaults to FLOAT32
            vector_index_algorithm (str): Indexing algorithm for vectors, defaults to HNSW
            query_dialect (int): Query dialect, must be 2 or greater for vector similarity searching, defaults to 2
            env_file_path (str | None): Use the environment settings file as a fallback to
                environment variables, defaults to False
            env_file_encoding (str | None): Encoding of the environment settings file, defaults to "utf-8"
        """
        try:
            redis_settings = RedisSettings(
                connection_string=connection_string,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise MemoryConnectorInitializationError("Failed to create Redis settings.", ex) from ex

        if vector_size <= 0:
            raise MemoryConnectorInitializationError("Vector dimension must be a positive integer")

        self._database = redis.Redis.from_url(redis_settings.connection_string.get_secret_value())
        self._ft = self._database.ft

        self._query_dialect = query_dialect
        self._vector_distance_metric = vector_distance_metric
        self._vector_index_algorithm = vector_index_algorithm
        self._vector_type_str = vector_type
        self._vector_type = np.float32 if vector_type == "FLOAT32" else np.float64
        self._vector_size = vector_size

    async def close(self):
        """Closes the Redis database connection."""
        logger.info("Closing Redis connection")
        self._database.close()

    async def create_collection(self, collection_name: str) -> None:
        """Creates a collection.

        Implemented as a Redis index containing hashes prefixed with "collection_name:".
        If a collection of the name exists, it is left unchanged.

        Args:
            collection_name (str): Name for a collection of embeddings
        """
        if await self.does_collection_exist(collection_name):
            logger.info(f'Collection "{collection_name}" already exists.')
        else:
            index_def = IndexDefinition(prefix=f"{collection_name}:", index_type=IndexType.HASH)
            schema = (
                TextField(name="key"),
                TextField(name="metadata"),
                TextField(name="timestamp"),
                VectorField(
                    name="embedding",
                    algorithm=self._vector_index_algorithm,
                    attributes={
                        "TYPE": self._vector_type_str,
                        "DIM": self._vector_size,
                        "DISTANCE_METRIC": self._vector_distance_metric,
                    },
                ),
            )

            try:
                self._ft(collection_name).create_index(definition=index_def, fields=schema)
            except Exception as e:
                raise ServiceResponseException(f"Failed to create collection {collection_name}") from e

    async def get_collections(self) -> list[str]:
        """Returns a list of names of all collection names present in the data store.

        Returns:
            List[str]: list of collection names
        """
        # Note: FT._LIST is a temporary command that may be deprecated in the future according to Redis
        return [name.decode() for name in self._database.execute_command("FT._LIST")]

    async def delete_collection(self, collection_name: str, delete_records: bool = True) -> None:
        """Deletes a collection from the data store.

        If the collection does not exist, the database is left unchanged.

        Args:
            collection_name (str): Name for a collection of embeddings
            delete_records (bool): Delete all data associated with the collection, default to True
        """
        if await self.does_collection_exist(collection_name):
            self._ft(collection_name).dropindex(delete_documents=delete_records)

    async def does_collection_exist(self, collection_name: str) -> bool:
        """Determines if a collection exists in the data store.

        Args:
            collection_name (str): Name for a collection of embeddings

        Returns:
            True if the collection exists, False if not
        """
        try:
            self._ft(collection_name).info()
            return True
        except ResponseError:
            return False

    async def upsert(self, collection_name: str, record: MemoryRecord) -> str:
        """Upsert a memory record into the data store.

        Does not guarantee that the collection exists.
            * If the record already exists, it will be updated.
            * If the record does not exist, it will be created.

        Note: if the record do not have the same dimensionality configured for the collection,
        it will not be detected to belong to the collection in Redis.

        Args:
            collection_name (str): Name for a collection of embeddings
            record (MemoryRecord): Memory record to upsert

        Returns:
            str: Redis key associated with the upserted memory record
        """
        if not await self.does_collection_exist(collection_name):
            raise ServiceResourceNotFoundError(f'Collection "{collection_name}" does not exist')

        # Typical Redis key structure: collection_name:{some identifier}
        record._key = get_redis_key(collection_name, record._id)

        # Overwrites previous data or inserts new key if not present
        # Index registers any hash matching its schema and prefixed with collection_name:
        try:
            self._database.hset(
                record._key,
                mapping=serialize_record_to_redis(record, self._vector_type),
            )
            return record._key
        except Exception as e:
            raise ServiceResponseException("Could not upsert messages.") from e

    async def upsert_batch(self, collection_name: str, records: list[MemoryRecord]) -> list[str]:
        """Upserts a group of memory records into the data store.

        Does not guarantee that the collection exists.
            * If the record already exists, it will be updated.
            * If the record does not exist, it will be created.

        Note: if the records do not have the same dimensionality configured for the collection,
        they will not be detected to belong to the collection in Redis.

        Args:
            collection_name (str): Name for a collection of embeddings
            records (List[MemoryRecord]): List of memory records to upsert

        Returns:
            List[str]: Redis keys associated with the upserted memory records
        """
        keys = list()
        for record in records:
            record_key = await self.upsert(collection_name, record)
            keys.append(record_key)

        return keys

    async def get(self, collection_name: str, key: str, with_embedding: bool = False) -> MemoryRecord:
        """Gets a memory record from the data store. Does not guarantee that the collection exists.

        Args:
            collection_name (str): Name for a collection of embeddings
            key (str): ID associated with the memory to get
            with_embedding (bool): Include embedding with the memory record, default to False

        Returns:
            MemoryRecord: The memory record if found, else None
        """
        if not await self.does_collection_exist(collection_name):
            raise ServiceResourceNotFoundError(f'Collection "{collection_name}" does not exist')

        internal_key = get_redis_key(collection_name, key)
        fields = self._database.hgetall(internal_key)

        # Did not find the record
        if len(fields) == 0:
            return None

        record = deserialize_redis_to_record(fields, self._vector_type, with_embedding)
        record._key = internal_key

        return record

    async def get_batch(
        self, collection_name: str, keys: list[str], with_embeddings: bool = False
    ) -> list[MemoryRecord]:
        """Gets a batch of memory records from the data store.

        Does not guarantee that the collection exists.

        Args:
            collection_name (str): Name for a collection of embeddings
            keys (List[str]): IDs associated with the memory records to get
            with_embeddings (bool): Include embeddings with the memory records, default to False

        Returns:
            List[MemoryRecord]: The memory records if found, else an empty list
        """
        records = list()
        for key in keys:
            record = await self.get(collection_name, key, with_embeddings)
            if record:
                records.append(record)

        return records

    async def remove(self, collection_name: str, key: str) -> None:
        """Removes a memory record from the data store.

        Does not guarantee that the collection exists.
        If the key does not exist, do nothing.

        Args:
            collection_name (str): Name for a collection of embeddings
            key (str): ID associated with the memory to remove
        """
        if not await self.does_collection_exist(collection_name):
            raise ServiceResourceNotFoundError(f'Collection "{collection_name}" does not exist')

        self._database.delete(get_redis_key(collection_name, key))

    async def remove_batch(self, collection_name: str, keys: list[str]) -> None:
        """Removes a batch of memory records from the data store. Does not guarantee that the collection exists.

        Args:
            collection_name (str): Name for a collection of embeddings
            keys (List[str]): IDs associated with the memory records to remove
        """
        if not await self.does_collection_exist(collection_name):
            raise ServiceResourceNotFoundError(f'Collection "{collection_name}" does not exist')

        self._database.delete(*[get_redis_key(collection_name, key) for key in keys])

    async def get_nearest_matches(
        self,
        collection_name: str,
        embedding: ndarray,
        limit: int,
        min_relevance_score: float = 0.0,
        with_embeddings: bool = False,
    ) -> list[tuple[MemoryRecord, float]]:
        """Get the nearest matches to an embedding using the configured similarity algorithm.

        Args:
            collection_name (str): Name for a collection of embeddings
            embedding (ndarray): Embedding to find the nearest matches to
            limit (int): Maximum number of matches to return
            min_relevance_score (float): Minimum relevance score of the matches, default to 0.0
            with_embeddings (bool): Include embeddings in the resultant memory records, default to False

        Returns:
            List[Tuple[MemoryRecord, float]]: Records and their relevance scores by descending
                order, or an empty list if no relevant matches are found
        """
        if not await self.does_collection_exist(collection_name):
            raise ServiceResourceNotFoundError(f'Collection "{collection_name}" does not exist')

        # Perform a k-nearest neighbors query, score by similarity
        query = (
            Query(f"*=>[KNN {limit} @embedding $embedding AS vector_score]")
            .dialect(self._query_dialect)
            .paging(offset=0, num=limit)
            .return_fields(
                "metadata",
                "timestamp",
                "embedding",
                "vector_score",
            )
            .sort_by("vector_score", asc=False)
        )
        query_params = {"embedding": embedding.astype(self._vector_type).tobytes()}
        matches = self._ft(collection_name).search(query, query_params).docs

        relevant_records = list()
        for match in matches:
            score = float(match["vector_score"])

            # Sorted by descending order
            if score < min_relevance_score:
                break

            record = deserialize_document_to_record(self._database, match, self._vector_type, with_embeddings)
            relevant_records.append((record, score))

        return relevant_records

    async def get_nearest_match(
        self,
        collection_name: str,
        embedding: ndarray,
        min_relevance_score: float = 0.0,
        with_embedding: bool = False,
    ) -> tuple[MemoryRecord, float]:
        """Get the nearest match to an embedding using the configured similarity algorithm.

        Args:
            collection_name (str): Name for a collection of embeddings
            embedding (ndarray): Embedding to find the nearest match to
            min_relevance_score (float): Minimum relevance score of the match, default to 0.0
            with_embedding (bool): Include embedding in the resultant memory record, default to False

        Returns:
            Tuple[MemoryRecord, float]: Record and the relevance score, or None if not found
        """
        matches = await self.get_nearest_matches(
            collection_name=collection_name,
            embedding=embedding,
            limit=1,
            min_relevance_score=min_relevance_score,
            with_embeddings=with_embedding,
        )

        return matches[0] if len(matches) else None
