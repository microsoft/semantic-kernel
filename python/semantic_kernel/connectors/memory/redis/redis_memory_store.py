# Copyright (c) Microsoft. All rights reserved.

from datetime import datetime
from logging import Logger
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from numpy import ndarray

import redis
from redis.commands.search.field import NumericField, TextField, VectorField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from redis.exceptions import ResponseError
from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.utils.null_logger import NullLogger


def redis_key(collection_name: str, key: str) -> str:
    """
    Returns the Redis key for an element called key within collection_name

    Arguments:
        collection_name {str} -- Name for a collection of embeddings
        key {str} -- ID associated with a memory record

    Returns:
        str -- Redis key in the format collection_name:key
    """
    return f"{collection_name}:{key}"


class RedisMemoryStore(MemoryStoreBase):
    """A memory store implementation using Redis"""

    _database: "redis.Redis"
    _vector_size: int
    _vector_type: "np.dtype"
    _ft: "redis.Redis.ft"
    _logger: Logger

    # For more information on vector attributes: https://redis.io/docs/stack/search/reference/vectors
    # Without RedisAI, it is currently not possible to retrieve index-specific vector attributes to have
    # fully independent collections. The user can chose a different vector dimensionality per collection,
    # but it is solely their responsibility to ensure proper dimensions of a vector to be indexed correctly.

    # Vector similarity index algorithm. The supported types are "FLAT" and "HNSW", the default being "HNSW".
    VECTOR_INDEX_ALGORITHM = "HNSW"

    # Type for vectors. The supported types are FLOAT32 and FLOAT64, the default being "FLOAT32"
    VECTOR_TYPE = "FLOAT32"

    # Metric for measuring vector distance. Supported types are L2, IP, COSINE, the default being "COSINE".
    VECTOR_DISTANCE_METRIC = "COSINE"

    # Query dialect. Must specify DIALECT 2 or higher to use a vector similarity query, the default being 2
    QUERY_DIALECT = 2

    def __init__(
        self,
        connection_string: str = "redis://localhost:6379",
        settings: Dict[str, Any] = None,
        logger: Optional[Logger] = None,
    ) -> None:
        """
        RedisMemoryStore is an abstracted interface to interact with a Redis node connection.
        See documentation about connections: https://redis-py.readthedocs.io/en/stable/connections.html

        Arguments:
            connection_string {str} -- Specify the connection string of the Redis connection, default to redis://localhost:6379
            settings {Dict[str, Any]} -- Configuration settings, default to None for a basic connection
            logger {Optional[Logger]} -- Logger, defaults to None

        Note:
            Connection parameters in settings may override connection_string if both are defined
        """

        self._database = redis.Redis.from_url(connection_string)
        if settings:
            self.configure(settings)
        assert self.ping(), "Redis could not establish a connection"

        self._ft = self._database.ft
        self._logger = logger or NullLogger()
        self._vector_type = (
            np.float32 if RedisMemoryStore.VECTOR_TYPE == "FLOAT32" else np.float64
        )

    def configure(self, settings: Dict[str, Any]) -> None:
        """
        Configures the Redis database connection.
        See documentation for accepted parameters: https://redis.io/commands/config-set/

        Arguments:
            settings {Dict[str, Any]} -- Desired configuration formatted each as {parameter: value}

        Example:
            ```
            # Create a default Redis data store
            redis_ds = RedisMemoryStore()

            # Set the host and port to be localhost:6369 and authenticate with the password "redis"
            redis_ds.configure({"bind":"localhost", "port":6379, password="redis"})
            ```

        Exceptions:
            Redis documentation for exceptions that can occur: https://redis.readthedocs.io/en/stable/exceptions.html
        """
        for param, val in settings.items():
            try:
                self._database.config_set(param, val)
            except Exception as e:
                self._logger.error(e)
                raise e

    def ping(self) -> bool:
        """
        Pings the Redis database connection.

        Returns:
            True if the connection is reachable, False if not
        """
        return self._database.ping()

    async def create_collection_async(
        self,
        collection_name: str,
        vector_dimension: int = 128,
    ) -> None:
        """
        Creates a collection, implemented as a Redis index containing hashes
        prefixed with "collection_name:".
        If a collection of the name exists, it is left unchanged.

        Note: vector dimensionality for a collection cannot be altered after creation.

        Arguments:
            collection_name {str} -- Name for a collection of embeddings
            vector_dimension {int} -- Size of each vector, default to 128
        """
        try:
            self._ft(collection_name).info()
            self._logger.info(f'Collection "{collection_name}" already exists.')
            print(f'Collection "{collection_name}" already exists.')
        except ResponseError:
            if vector_dimension <= 0:
                self._logger.error("Vector dimension must be a positive integer")
                raise Exception("Vector dimension must be a positive integer")

            index_def = IndexDefinition(
                prefix=f"{collection_name}:", index_type=IndexType.HASH
            )
            schema = (
                TextField(name="timestamp"),
                NumericField(name="is_reference"),
                TextField(name="external_source_name"),
                TextField(name="id"),
                TextField(name="description"),
                TextField(name="text"),
                TextField(name="additional_metadata"),
                VectorField(
                    name="embedding",
                    algorithm=RedisMemoryStore.VECTOR_INDEX_ALGORITHM,
                    attributes={
                        "TYPE": RedisMemoryStore.VECTOR_TYPE,
                        "DIM": vector_dimension,
                        "DISTANCE_METRIC": RedisMemoryStore.VECTOR_DISTANCE_METRIC,
                    },
                ),
            )

            try:
                self._ft(collection_name).create_index(
                    definition=index_def, fields=schema
                )
            except Exception as e:
                self._logger.error(e)
                raise e

    async def get_collections_async(self) -> List[str]:
        """
        Returns a list of names of all collection names present in the data store.

        Returns:
            List[str]  -- list of collection names
        """
        # Note: FT._LIST is a temporary command that may be deprecated in the future according to Redis
        return [name.decode() for name in self._database.execute_command("FT._LIST")]

    async def delete_collection_async(
        self, collection_name: str, delete_records: bool = True
    ) -> None:
        """
        Deletes a collection from the data store.
        If the collection does not exist, the database is left unchanged.

        Arguments:
            collection_name {str} -- Name for a collection of embeddings
            delete_records {bool} -- Delete all data associated with the collection, default to True

        """
        if await self.does_collection_exist_async(collection_name):
            self._ft(collection_name).dropindex(delete_documents=delete_records)

    async def delete_all_collections_async(self, delete_records: bool = True) -> None:
        """
        Deletes all collections present in the data store.

        Arguments:
            delete_records {bool} -- Delete all data associated with the collections, default to True
        """
        for col_name in await self.get_collections_async():
            self._ft(col_name).dropindex(delete_documents=delete_records)

    async def does_collection_exist_async(self, collection_name: str) -> bool:
        """
        Determines if a collection exists in the data store.

        Arguments:
            collection_name {str} -- Name for a collection of embeddings

        Returns:
            True if the collection exists, False if not
        """
        try:
            self._ft(collection_name).info()
            return True
        except ResponseError:
            return False

    async def upsert_async(self, collection_name: str, record: MemoryRecord) -> str:
        """
        Upsert a memory record into the data store. Does not guarantee that the collection exists.
            * If the record already exists, it will be updated.
            * If the record does not exist, it will be created.

        Note: if the record do not have the same dimensionality configured for the collection,
        it will not be detected to belong to the collection in Redis.

        Arguments:
            collection_name {str} -- Name for a collection of embeddings
            record {MemoryRecord} -- Memory record to upsert

        Returns
            str -- Redis key associated with the upserted memory record, or None if an error occured
        """
        batch = await self.upsert_batch_async(collection_name, [record])
        return batch[0] if len(batch) else None

    async def upsert_batch_async(
        self, collection_name: str, records: List[MemoryRecord]
    ) -> List[str]:
        """
        Upserts a group of memory records into the data store. Does not guarantee that the collection exists.
            * If the record already exists, it will be updated.
            * If the record does not exist, it will be created.

        Note: if the records do not have the same dimensionality configured for the collection,
        they will not be detected to belong to the collection in Redis.

        Arguments:
            collection_name {str} -- Name for a collection of embeddings
            records {List[MemoryRecord]} -- List of memory records to upsert

        Returns
            List[str] -- Redis keys associated with the upserted memory records, or an empty list if an error occured
        """

        if not await self.does_collection_exist_async(collection_name):
            self._logger.error(f'Collection "{collection_name}" does not exist')
            raise Exception(f'Collection "{collection_name}" does not exist')

        keys = list()
        for rec in records:
            # Typical Redis key structure: collection_name:{some identifier}
            rec._key = redis_key(collection_name, rec._id)

            # Overwrites previous data or inserts new key if not present
            # Index registers any hash matching its schema and prefixed with collection_name:
            self._database.hset(
                rec._key,
                mapping=self._serialize_record_to_redis(rec),
            )
            keys.append(rec._key)

        return keys

    async def get_async(
        self, collection_name: str, key: str, with_embedding: bool = False
    ) -> MemoryRecord:
        """
        Gets a memory record from the data store. Does not guarantee that the collection exists.

        Arguments:
            collection_name {str} -- Name for a collection of embeddings
            key {str} -- ID associated with the memory to get
            with_embedding {bool} -- Include embedding with the memory record, default to False

        Returns:
            MemoryRecord -- The memory record if found, else None
        """

        batch = await self.get_batch_async(collection_name, [key], with_embedding)
        return batch[0] if len(batch) else None

    async def get_batch_async(
        self, collection_name: str, keys: List[str], with_embeddings: bool = False
    ) -> List[MemoryRecord]:
        """
        Gets a batch of memory records from the data store. Does not guarantee that the collection exists.

        Arguments:
            collection_name {str} -- Name for a collection of embeddings
            keys {List[str]} -- IDs associated with the memory records to get
            with_embedding {bool} -- Include embeddings with the memory records, default to False

        Returns:
            List[MemoryRecord] -- The memory records if found, else an empty list
        """
        if not await self.does_collection_exist_async(collection_name):
            self._logger.error(f'Collection "{collection_name}" does not exist')
            raise Exception(f'Collection "{collection_name}" does not exist')

        records = list()
        for key in keys:
            internal_key = redis_key(collection_name, key)
            raw_fields = self._database.hgetall(internal_key)

            # Did not find the record
            if len(raw_fields) == 0:
                continue

            rec = self._deserialize_redis_to_record(raw_fields, with_embeddings)
            rec._key = internal_key
            records.append(rec)

        return records

    async def remove_async(self, collection_name: str, key: str) -> None:
        """
        Removes a memory record from the data store. Does not guarantee that the collection exists.
        If the key does not exist, do nothing.

        Arguments:
            collection_name {str} -- Name for a collection of embeddings
            key {str} -- ID associated with the memory to remove
        """
        if not await self.does_collection_exist_async(collection_name):
            self._logger.error(f'Collection "{collection_name}" does not exist')
            raise Exception(f'Collection "{collection_name}" does not exist')

        self._database.delete(redis_key(collection_name, key))

    async def remove_batch_async(self, collection_name: str, keys: List[str]) -> None:
        """
        Removes a batch of memory records from the data store. Does not guarantee that the collection exists.

        Arguments:
            collection_name {str} -- Name for a collection of embeddings
            keys {List[str]} -- IDs associated with the memory records to remove
        """
        if not await self.does_collection_exist_async(collection_name):
            self._logger.error(f'Collection "{collection_name}" does not exist')
            raise Exception(f'Collection "{collection_name}" does not exist')

        self._database.delete(*[redis_key(collection_name, key) for key in keys])

    async def get_nearest_matches_async(
        self,
        collection_name: str,
        embedding: ndarray,
        limit: int,
        min_relevance_score: float = 0.0,
        with_embeddings: bool = False,
    ) -> List[Tuple[MemoryRecord, float]]:
        """
        Get the nearest matches to an embedding using the configured similarity algorithm, which is
        defaulted to cosine similarity.

        Arguments:
            collection_name {str} -- Name for a collection of embeddings
            embedding {ndarray} -- Embedding to find the nearest matches to
            limit {int} -- Maximum number of matches to return
            min_relevance_score {float} -- Minimum relevance score of the matches, default to 0.0
            with_embeddings {bool} -- Include embeddings in the resultant memory records, default to False

        Returns:
            List[Tuple[MemoryRecord, float]] -- Records and their relevance scores by descending
                order, or an empty list if no relevant matches are found
        """
        if not await self.does_collection_exist_async(collection_name):
            self._logger.error(f'Collection "{collection_name}" does not exist')
            raise Exception(f'Collection "{collection_name}" does not exist')

        query = (
            Query(f"*=>[KNN {limit} @embedding $embedding AS vector_score]")
            .dialect(RedisMemoryStore.QUERY_DIALECT)
            .paging(offset=0, num=limit)
            .return_fields(
                "id",
                "text",
                "description",
                "additional_metadata",
                "embedding",
                "timestamp",
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

            record = self._deserialize_document_to_record(match, with_embeddings)
            relevant_records.append((record, score))

        return relevant_records

    async def get_nearest_match_async(
        self,
        collection_name: str,
        embedding: ndarray,
        min_relevance_score: float = 0.0,
        with_embedding: bool = False,
    ) -> Tuple[MemoryRecord, float]:
        """
        Get the nearest match to an embedding using the configured similarity algorithm, which is
        defaulted to cosine similarity.

        Arguments:
            collection_name {str} -- Name for a collection of embeddings
            embedding {ndarray} -- Embedding to find the nearest match to
            min_relevance_score {float} -- Minimum relevance score of the match, default to 0.0
            with_embedding {bool} -- Include embedding in the resultant memory record, default to False

        Returns:
            Tuple[MemoryRecord, float] -- Record and the relevance score, or None if not found
        """
        matches = await self.get_nearest_matches_async(
            collection_name=collection_name,
            embedding=embedding,
            limit=1,
            min_relevance_score=min_relevance_score,
            with_embeddings=with_embedding,
        )

        return matches[0] if len(matches) else None

    def _serialize_record_to_redis(self, record: MemoryRecord) -> Dict[str, Any]:
        if not record._key:
            self._logger.error("Record must have a valid key associated with it")
            raise Exception("Record must have a valid key associated with it")

        mapping = {
            "timestamp": record._timestamp.isoformat() if record._timestamp else "",
            "is_reference": 1 if record._is_reference else 0,
            "external_source_name": record._external_source_name or "",
            "id": record._id or "",
            "description": record._description or "",
            "text": record._text or "",
            "additional_metadata": record._additional_metadata or "",
            "embedding": (
                record._embedding.astype(self._vector_type).tobytes()
                if record._embedding is not None
                else ""
            ),
        }
        return mapping

    def _deserialize_redis_to_record(
        self, fields: Dict[str, Any], with_embedding: bool
    ) -> MemoryRecord:
        if not fields.get(b"id"):
            self._logger.error("ID not present in serialized data")
            raise Exception("ID not present in serialized data")

        record = MemoryRecord(
            id=fields[b"id"].decode(),
            is_reference=bool(int(fields[b"is_reference"].decode())),
            external_source_name=fields[b"external_source_name"].decode(),
            description=fields[b"description"].decode(),
            text=fields[b"text"].decode(),
            additional_metadata=fields[b"additional_metadata"].decode(),
            embedding=None,
        )

        if fields[b"timestamp"] != b"":
            record._timestamp = datetime.fromisoformat(fields[b"timestamp"].decode())

        if with_embedding:
            # Extract using the vector type, then convert to regular Python float type
            record._embedding = np.frombuffer(
                fields[b"embedding"], dtype=self._vector_type
            ).astype(float)

        return record

    def _deserialize_document_to_record(
        self, doc: redis.commands.search.document.Document, with_embedding: bool
    ) -> MemoryRecord:
        # Parse collection name out of ID
        key_str = doc["id"]
        colon_index = key_str.index(":")
        id_str = key_str[colon_index + 1 :]

        record = MemoryRecord.local_record(
            id=id_str,
            text=doc["text"],
            description=doc["description"],
            additional_metadata=doc["additional_metadata"],
            embedding=None,
            timestamp=None,
        )

        if doc["timestamp"] != "":
            record._timestamp = datetime.fromisoformat(doc["timestamp"])

        if with_embedding:
            # Some bytes are lost when retrieving a document, fetch raw embedding
            eb = self._database.hget(key_str, "embedding")
            record._embedding = np.frombuffer(eb, dtype=self._vector_type).astype(float)

        return record
