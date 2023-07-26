# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import List, Optional, Tuple

import numpy as np
from numpy import ndarray

import redis
from redis.commands.search.field import NumericField, TextField, VectorField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from redis.exceptions import ResponseError
from semantic_kernel.connectors.memory.redis.utils import (
    deserialize_document_to_record,
    deserialize_redis_to_record,
    redis_key,
    serialize_record_to_redis,
)
from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.utils.null_logger import NullLogger


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
        database: redis.Redis,
        logger: Optional[Logger] = None,
    ) -> None:
        """
        RedisMemoryStore is an abstracted interface to interact with a Redis node connection.
        See documentation about connections: https://redis-py.readthedocs.io/en/stable/connections.html

        Arguments:
            database {redis.Redis} -- Provide specific instance of a Redis connection
            logger {Optional[Logger]} -- Logger, defaults to None

        """

        self._database = database
        self._ft = self._database.ft
        self._logger = logger or NullLogger()
        self._vector_type = (
            np.float32 if RedisMemoryStore.VECTOR_TYPE == "FLOAT32" else np.float64
        )

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

        if not await self.does_collection_exist_async(collection_name):
            self._logger.error(f'Collection "{collection_name}" does not exist')
            raise Exception(f'Collection "{collection_name}" does not exist')

        # Typical Redis key structure: collection_name:{some identifier}
        record._key = redis_key(collection_name, record._id)

        # Overwrites previous data or inserts new key if not present
        # Index registers any hash matching its schema and prefixed with collection_name:
        try:
            self._database.hset(
                record._key,
                mapping=serialize_record_to_redis(record, self._vector_type),
            )
            return record._key
        except Exception:
            return None

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

        keys = list()
        for record in records:
            rec_key = await self.upsert_async(collection_name, record)
            if rec_key:
                keys.append(rec_key)

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

        if not await self.does_collection_exist_async(collection_name):
            self._logger.error(f'Collection "{collection_name}" does not exist')
            raise Exception(f'Collection "{collection_name}" does not exist')

        internal_key = redis_key(collection_name, key)
        raw_fields = self._database.hgetall(internal_key)

        # Did not find the record
        if len(raw_fields) == 0:
            return None

        record = deserialize_redis_to_record(
            raw_fields, self._vector_type, with_embedding
        )
        record._key = internal_key

        return record

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

        records = list()
        for key in keys:
            record = await self.get_async(collection_name, key, with_embeddings)
            if record:
                records.append(record)

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

            record = deserialize_document_to_record(
                self._database, match, self._vector_type, with_embeddings
            )
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
