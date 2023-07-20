# Copyright (c) Microsoft. All rights reserved.

from datetime import datetime
from logging import Logger
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from numpy import ndarray

import redis
from redis.commands.search.field import NumericField, TextField, VectorField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.exceptions import ResponseError
from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.utils.null_logger import NullLogger


class RedisMemoryStore(MemoryStoreBase):
    """A memory store implmentation using Redis"""

    _database: "redis.Redis"
    _vector_size: int
    _ft: "redis.Redis.ft"
    _logger: Logger

    # For more information on vector attributes: https://redis.io/docs/stack/search/reference/vectors
    # Vector similarity index algorithm. The default value is "HNSW".
    VECTOR_INDEX_ALGORITHM = "HNSW"

    # Type for vectors. The supported types are FLOAT32 and FLOAT64. The default is "FLOAT32"
    VECTOR_TYPE = "FLOAT32"

    # Metric for measuring vector distance. Supported types are L2, IP, COSINE. The default is "COSINE".
    VECTOR_DISTANCE_METRIC = "COSINE"

    # Query dialect. Must specify DIALECT 2 or higher to use a vector similarity query. The defualt value is 2
    QUERY_DIALECT = 2

    def __init__(
        self,
        connection_string: str = None,
        database: redis.Redis = None,
        settings: Dict[str, Any] = None,
        vector_size: int = 128,
        logger: Optional[Logger] = None,
    ) -> None:
        """
        RedisMemoryStore is an abstracted interface to interact with a Redis node connection.
        Consult the [Redis documentation](https://redis-py.readthedocs.io/en/stable/connections.html)
        for more details about Redis connections.

        Arguments:
            * `connection_string` {str} -- Specify the connection string of the Redis connection
            * `database` {redis.Redis} -- Provide specific instance of a Redis connection
            * `settings`  {Dict[str, Any]} -- Configuration settings for the Redis instance
            * `vector_size` {int} -- Dimension of vectors within the database, default to 128

            Note: configuration is priortized from database < connection_string < settings
                if at least 2/3 of these are specified
        """

        self._database = (
            redis.Redis.from_url(connection_string)
            if connection_string
            else (database if database else redis.Redis())
        )
        if settings:
            self.configure(settings)
        assert self._database.ping(), "Redis could not establish a connection"

        assert vector_size > 0, "Vector dimension must be positive integer"
        self._vector_size = vector_size
        self._ft = self._database.ft

        self._logger = logger or NullLogger()

    def configure(self, settings: Dict[str, Any]) -> None:
        """
        Configures the Redis database connection, consult the [Redis documentation](https://redis.io/commands/config-set/)
        for further information on accepted parameters.

        Arguments:
            * `settings` {Dict[str, Any]} -- Desired configuration formatted each as {parameter: value}

        Example:
            ```
            # Create a default Redis data store
            redis_ds = RedisMemoryStore()

            # Set the host and port to be localhost:6369 and authenticate with the password "redis"
            redis_ds.configure({"bind":"localhost", "port":6379, password="redis"})
            ```

        Exceptions:
            Consult the [Redis documentation](https://redis.readthedocs.io/en/stable/exceptions.html) for further
            details on the exceptions that can occur.
        """
        for param, val in settings.items():
            self._database.config_set(param, val)

    async def create_collection_async(self, collection_name: str) -> None:
        """
        Creates a collection implemented as a Redis hash index.
        Each element of the collection is prefixed with  "collection_name:"
        If a collection of the name already exists, it is left unchanged.

        Arguments:
            * `collection_name` {str} -- Name for a collection of embeddings
        """

        try:
            self._ft(collection_name).info()
            print(f'Collection "{collection_name}" already exists.')
        except ResponseError:
            index_definition = IndexDefinition(
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
                        "DIM": self._vector_size,
                        "DISTANCE_METRIC": RedisMemoryStore.VECTOR_DISTANCE_METRIC,
                    },
                ),
            )

            self._ft(collection_name).create_index(
                definition=index_definition, fields=schema
            )

    async def get_collections_async(self) -> List[str]:
        """
        Get all collection names in the data store.

        Returns:
            List[str] -- list of collection names
        """
        # Note: FT._LIST is a temporary command that may be deprecated in the future according to Redis
        return [name.decode() for name in self._database.execute_command("FT._LIST")]

    async def delete_collection_async(self, collection_name: str) -> None:
        """
        Deletes a collection and all its data from the data store.
        If the collection does not exist, the database is left unchanged.

        Arguments:
            * `collection_name` {str} -- Name for a collection of embeddings

        """
        if await self.does_collection_exist_async(collection_name):
            self._ft(collection_name).dropindex(delete_documents=True)

    async def does_collection_exist_async(self, collection_name: str) -> bool:
        """
        Determines if a collection exists in the data store.

        Arguments:
            * `collection_name` {str} -- Name for a collection of embeddings

        Returns:
            `True` if the collection exists, `False` if not
        """
        try:
            self._ft(collection_name).info()
            return True
        except ResponseError:
            return False

    async def upsert_async(self, collection_name: str, record: MemoryRecord) -> str:
        """
        Upsert a memory record into the data store. Does not gurantee that the collection exists.
            If the record already exists, it will be updated.
            If the record does not exist, it will be created.

        Arguemnts:
            collection_name {str} -- Name for a collection of embeddings
            record {MemoryRecord} -- Memory record to upsert

        Returns
            str -- The unique identifier for the memory record, which is the Redis key
        """

        batch = await self.upsert_batch_async(collection_name, [record])
        return batch[0] if len(batch) else None

    async def upsert_batch_async(
        self, collection_name: str, records: List[MemoryRecord]
    ) -> List[str]:
        """
        Upserts a group of memory records into the data store. Does not gurantee that the collection exists.
            If the record already exists, it will be updated.
            If the record does not exist, it will be created.

        Arguemnts:
            collection_name {str} -- Name for a collection of embeddings
            records {List[MemoryRecords]} -- Memory records to upsert

        Returns
            List[str] -- The unique identifiers for the memory records, which are the Redis keys
        """

        if not await self.does_collection_exist_async(collection_name):
            raise Exception(f"Collection '{collection_name}' does not exist")

        keys = list()
        for rec in records:
            # Typical Redis key structure: collection_name:{some identifier}
            rec._key = f"{collection_name}:{rec._id}"

            # Overwrites previous data or inserts new key if not present
            # Index registers any hash matching its schema and prefixed with collection_name:
            self._database.hset(
                rec._key,
                mapping=self._serialize_record(rec),
            )
            keys.append(rec._key)

        return keys

    async def get_async(
        self, collection_name: str, key: str, with_embedding: bool
    ) -> MemoryRecord:
        """
        Gets a memory record from the data store. Does not guarantee that the collection exists.

        Arguments:
            collection_name {str} -- Name for a collection of embeddings
            key {str} -- Unique id associated with the memory record to get
            with_embedding {bool} -- If true, the embedding will be returned in the memory record

        Returns:
            MemoryRecord -- The memory record if found, else None
        """

        batch = await self.get_batch_async(collection_name, [key], with_embedding)
        return batch[0] if len(batch) else None

    async def get_batch_async(
        self, collection_name: str, keys: List[str], with_embeddings: bool
    ) -> List[MemoryRecord]:
        """
        Gets a batch of memory records from the data store. Does not guarantee that the collection exists

        Arguments:
            collection_name {str} -- Name for a collection of embeddings
            keys {List[str]} -- Unique ids associated with the memory records to get
            with_embedding {bool} -- If true, the embeddings will be returned in the memory records

        Returns:
            List[MemoryRecord] -- The memory records if found, else an empty list
        """
        if not await self.does_collection_exist_async(collection_name):
            raise Exception(f"Collection '{collection_name}' does not exist")

        records = list()
        for key in keys:
            internal_key = f"{collection_name}:{key}"
            raw_fields = self._database.hgetall(internal_key)

            # Did not find the record
            if len(raw_fields) == 0:
                continue

            rec = self._deserialize_record(raw_fields, with_embeddings)
            rec._key = internal_key
            records.append(rec)

        return records

    async def remove_async(self, collection_name: str, key: str) -> None:
        """
        Removes a memory record from the data store. Does not guarantee that the collection exists.
        If the key does not exist, do nothing.

        Arguments:
            collection_name {str} -- Name for a collection of embeddings
            key {str} -- Unique id associated with the memory record to remove
        """
        if not await self.does_collection_exist_async(collection_name):
            raise Exception(f"Collection '{collection_name}' does not exist")

        self._database.delete(f"{collection_name}:{key}")

    async def remove_batch_async(self, collection_name: str, keys: List[str]) -> None:
        """
        Removes a batch of memory records from the data store. Does not guarantee that the collection exists.

        Arguments:
            collection_name {str} -- Name for a collection of embeddings
            keys {List[str]} -- Unique ids associated with the memory records to remove
        """
        if not await self.does_collection_exist_async(collection_name):
            raise Exception(f"Collection '{collection_name}' does not exist")

        self._database.delete([f"{collection_name}:{key}" for key in keys])

    async def get_nearest_matches_async(
        self,
        collection_name: str,
        embedding: ndarray,
        limit: int,
        min_relevance_score: float = 0.0,
        with_embeddings: bool = True,
    ) -> List[Tuple[MemoryRecord, float]]:
        pass

    async def get_nearest_match_async(
        self,
        collection_name: str,
        embedding: ndarray,
        min_relevance_score: float = 0.0,
        with_embedding: bool = True,
    ) -> Tuple[MemoryRecord, float]:
        pass

    def _serialize_record(self, record: MemoryRecord) -> Dict[str, Any]:
        """
        Helper function to serialize a record into a Redis mapping (excluding its key)
        """
        assert record._key, "Error: Record must have a valid key"

        mapping = {
            "timestamp": record._timestamp.isoformat(sep=" ") or "",
            "is_reference": int(record._is_reference) or 0,
            "external_source_name": record._external_source_name or "",
            "id": record._id or "",
            "description": record._description or "",
            "text": record._text or "",
            "additional_metadata": record._additional_metadata or "",
            "embedding": record._embedding.astype(self._vector_type()).tobytes() or "",
        }
        return mapping

    def _deserialize_record(
        self, fields: Dict[str, Any], with_embedding: bool
    ) -> MemoryRecord:
        """
        Helper function to deserialize a record from a Redis mapping
        """
        assert fields.get(b"id", None), "Error: id not present in serialized data"

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
                fields[b"embedding"], dtype=self._vector_type()
            ).astype(float)

        return record

    def _vector_type(self):
        return np.float32 if RedisMemoryStore.VECTOR_TYPE == "FLOAT32" else np.float64
