# Copyright (c) Microsoft. All rights reserved.

import atexit
import json
from logging import Logger
from typing import List, Optional, Tuple

import numpy as np
from numpy import ndarray
from psycopg import Cursor
from psycopg.sql import SQL, Identifier
from psycopg_pool import ConnectionPool

from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.utils.null_logger import NullLogger

# Limitation based on pgvector documentation https://github.com/pgvector/pgvector#what-if-i-want-to-index-vectors-with-more-than-2000-dimensions
MAX_DIMENSIONALITY = 2000
DEFAULT_SCHEMA = "public"


class PostgresMemoryStore(MemoryStoreBase):
    """A memory store that uses Postgres with pgvector as the backend."""

    _connection_string: str
    _connection_pool: ConnectionPool
    _default_dimensionality: int
    _schema: str
    _logger: Logger

    def __init__(
        self,
        connection_string: str,
        default_dimensionality: int,
        min_pool: int,
        max_pool: int,
        schema: str = DEFAULT_SCHEMA,
        logger: Optional[Logger] = None,
    ) -> None:
        """Initializes a new instance of the PostgresMemoryStore class.

        Arguments:
            connection_string {str} -- The connection string to the Postgres database.\n
            default_dimensionality {int} -- The default dimensionality of the embeddings.\n
            min_pool {int} -- The minimum number of connections in the connection pool.\n
            max_pool {int} -- The maximum number of connections in the connection pool.\n
            schema {str} -- The schema to use. (default: {"public"})\n
            timezone_offset {Optional[str]} -- The timezone offset to use. (default: {None})
            Expected format '-7:00'. Uses the local timezone offset when not provided.\n
            logger {Optional[Logger]} -- The logger to use. (default: {None})
        """

        self._check_dimensionality(default_dimensionality)

        self._connection_string = connection_string
        self._default_dimensionality = default_dimensionality
        self._connection_pool = ConnectionPool(
            self._connection_string, min_size=min_pool, max_size=max_pool
        )
        self._schema = schema
        atexit.register(self._connection_pool.close)
        self._logger = logger or NullLogger()

    async def create_collection_async(
        self,
        collection_name: str,
        dimension_num: Optional[int] = None,
    ) -> None:
        """Creates a new collection.

        Arguments:
            collection_name {str} -- The name of the collection to create.\n
            dimension_num {Optional[int]} -- The dimensionality of the embeddings. (default: {None})
            Uses the default dimensionality when not provided

        Returns:
            None
        """
        if dimension_num is None:
            dimension_num = self._default_dimensionality
        else:
            self._check_dimensionality(dimension_num)

        with self._connection_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    SQL(
                        """
                        CREATE TABLE IF NOT EXISTS {scm}.{tbl} (
                            key TEXT PRIMARY KEY,
                            embedding vector({dim}),
                            metadata JSONB,
                            timestamp TIMESTAMP
                        )"""
                    ).format(
                        scm=Identifier(self._schema),
                        tbl=Identifier(collection_name),
                        dim=dimension_num,
                    ),
                    (),
                )

    async def get_collections_async(self) -> List[str]:
        """Gets the list of collections.

        Returns:
            List[str] -- The list of collections.
        """
        with self._connection_pool.connection() as conn:
            with conn.cursor() as cur:
                return await self.__get_collections_async(cur)

    async def delete_collection_async(self, collection_name: str) -> None:
        """Deletes a collection.

        Arguments:
            collection_name {str} -- The name of the collection to delete.

        Returns:
            None
        """
        with self._connection_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    SQL("DROP TABLE IF EXISTS {scm}.{tbl} CASCADE").format(
                        scm=Identifier(self._schema), tbl=Identifier(collection_name)
                    ),
                )

    async def does_collection_exist_async(self, collection_name: str) -> bool:
        """Checks if a collection exists.

        Arguments:
            collection_name {str} -- The name of the collection to check.

        Returns:
            bool -- True if the collection exists; otherwise, False.
        """
        with self._connection_pool.connection() as conn:
            with conn.cursor() as cur:
                return await self.__does_collection_exist_async(cur, collection_name)

    async def upsert_async(self, collection_name: str, record: MemoryRecord) -> str:
        """Upserts a record.

        Arguments:
            collection_name {str} -- The name of the collection to upsert the record into.\n
            record {MemoryRecord} -- The record to upsert.

        Returns:
            str -- The unique database key of the record. In Pinecone, this is the record ID.
        """
        with self._connection_pool.connection() as conn:
            with conn.cursor() as cur:
                if not await self.__does_collection_exist_async(cur, collection_name):
                    raise Exception(f"Collection '{collection_name}' does not exist")
                cur.execute(
                    SQL(
                        """
                        INSERT INTO {scm}.{tbl} (key, embedding, metadata, timestamp)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (key) DO UPDATE
                        SET embedding = EXCLUDED.embedding,
                            metadata = EXCLUDED.metadata,
                            timestamp = EXCLUDED.timestamp
                        RETURNING key
                        """
                    ).format(
                        scm=Identifier(self._schema),
                        tbl=Identifier(collection_name),
                    ),
                    (
                        record._id,
                        record.embedding.tolist(),
                        self.__serialize_metadata(record),
                        record._timestamp,
                    ),
                )
                result = cur.fetchone()
                if result is None:
                    raise Exception("Upsert failed")
                return result[0]

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
        with self._connection_pool.connection() as conn:
            with conn.cursor() as cur:
                if not await self.__does_collection_exist_async(cur, collection_name):
                    raise Exception(f"Collection '{collection_name}' does not exist")
                cur.nextset()
                cur.executemany(
                    SQL(
                        """
                        INSERT INTO {scm}.{tbl} (key, embedding, metadata, timestamp)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (key) DO UPDATE
                        SET embedding = EXCLUDED.embedding,
                            metadata = EXCLUDED.metadata,
                            timestamp = EXCLUDED.timestamp
                        RETURNING key
                        """
                    ).format(
                        scm=Identifier(self._schema),
                        tbl=Identifier(collection_name),
                    ),
                    [
                        (
                            record._id,
                            record.embedding.tolist(),
                            self.__serialize_metadata(record),
                            record._timestamp,
                        )
                        for record in records
                    ],
                    returning=True,
                )

                # collate results
                results = [cur.fetchone()]
                while cur.nextset():
                    results.append(cur.fetchone())
                if None in results:
                    raise Exception("Upsert failed")
                return [result[0] for result in results if result is not None]

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
        with self._connection_pool.connection() as conn:
            with conn.cursor() as cur:
                if not await self.__does_collection_exist_async(cur, collection_name):
                    raise Exception(f"Collection '{collection_name}' does not exist")
                cur.execute(
                    SQL(
                        """
                        SELECT key, embedding, metadata, timestamp
                        FROM {scm}.{tbl}
                        WHERE key = %s
                        """
                    ).format(
                        scm=Identifier(self._schema),
                        tbl=Identifier(collection_name),
                    ),
                    (key,),
                )
                result = cur.fetchone()
                if result is None:
                    raise KeyError("Key not found")
                return MemoryRecord.local_record(
                    id=result[0],
                    embedding=np.fromstring(result[1].strip("[]"), dtype=float, sep=",")
                    if with_embedding
                    else np.array([]),
                    text=result[2]["text"],
                    description=result[2]["description"],
                    additional_metadata=result[2]["additional_metadata"],
                    timestamp=result[3],
                )

    async def get_batch_async(
        self, collection_name: str, keys: List[str], with_embeddings: bool = False
    ) -> List[MemoryRecord]:
        """Gets a batch of records.

        Arguments:
            collection_name {str} -- The name of the collection to get the records from.
            keys {List[str]} -- The unique database keys of the records.
            with_embeddings {bool} -- Whether to include the embeddings in the results. (default: {False})

        Returns:
            List[MemoryRecord] -- The records that were found from list of keys, can be empty.
        """
        with self._connection_pool.connection() as conn:
            with conn.cursor() as cur:
                if not await self.__does_collection_exist_async(cur, collection_name):
                    raise Exception(f"Collection '{collection_name}' does not exist")
                cur.execute(
                    SQL(
                        """
                        SELECT key, embedding, metadata, timestamp
                        FROM {scm}.{tbl}
                        WHERE key = ANY(%s)
                        """
                    ).format(
                        scm=Identifier(self._schema),
                        tbl=Identifier(collection_name),
                    ),
                    (list(keys),),
                )
                results = cur.fetchall()
                return [
                    MemoryRecord.local_record(
                        id=result[0],
                        embedding=np.fromstring(
                            result[1].strip("[]"), dtype=float, sep=","
                        )
                        if with_embeddings
                        else np.array([]),
                        text=result[2]["text"],
                        description=result[2]["description"],
                        additional_metadata=result[2]["additional_metadata"],
                        timestamp=result[3],
                    )
                    for result in results
                ]

    async def remove_async(self, collection_name: str, key: str) -> None:
        """Removes a record.

        Arguments:
            collection_name {str} -- The name of the collection to remove the record from.
            key {str} -- The unique database key of the record to remove.

        Returns:
            None
        """
        with self._connection_pool.connection() as conn:
            with conn.cursor() as cur:
                if not await self.__does_collection_exist_async(cur, collection_name):
                    raise Exception(f"Collection '{collection_name}' does not exist")
                cur.execute(
                    SQL(
                        """
                        DELETE FROM {scm}.{tbl}
                        WHERE key = %s
                        """
                    ).format(
                        scm=Identifier(self._schema), tbl=Identifier(collection_name)
                    ),
                    (key,),
                )

    async def remove_batch_async(self, collection_name: str, keys: List[str]) -> None:
        """Removes a batch of records.

        Arguments:
            collection_name {str} -- The name of the collection to remove the records from.
            keys {List[str]} -- The unique database keys of the records to remove.

        Returns:
            None
        """
        with self._connection_pool.connection() as conn:
            with conn.cursor() as cur:
                if not await self.__does_collection_exist_async(cur, collection_name):
                    raise Exception(f"Collection '{collection_name}' does not exist")
                cur.execute(
                    SQL(
                        """
                        DELETE FROM {scm}.{tbl}
                        WHERE key = ANY(%s)
                        """
                    ).format(
                        scm=Identifier(self._schema), tbl=Identifier(collection_name)
                    ),
                    (list(keys),),
                )

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
        with self._connection_pool.connection() as conn:
            with conn.cursor() as cur:
                if not await self.__does_collection_exist_async(cur, collection_name):
                    raise Exception(f"Collection '{collection_name}' does not exist")
                cur.execute(
                    SQL(
                        """
                        SELECT key,
                            embedding,
                            metadata,
                            cosine_similarity,
                            timestamp
                        FROM (
                            SELECT key, embedding, metadata, 1 - (embedding <=> '[{emb}]') \
                                AS cosine_similarity, timestamp
                            FROM {scm}.{tbl}
                        ) AS subquery
                        WHERE cosine_similarity >= {mrs}
                        ORDER BY cosine_similarity DESC
                        LIMIT {limit}
                        """
                    ).format(
                        scm=Identifier(self._schema),
                        tbl=Identifier(collection_name),
                        mrs=min_relevance_score,
                        limit=limit,
                        emb=SQL(",").join(embedding.tolist()),
                    )
                )
                results = cur.fetchall()

                return [
                    (
                        MemoryRecord.local_record(
                            id=result[0],
                            embedding=np.fromstring(
                                result[1].strip("[]"), dtype=float, sep=","
                            )
                            if with_embeddings
                            else np.array([]),
                            text=result[2]["text"],
                            description=result[2]["description"],
                            additional_metadata=result[2]["additional_metadata"],
                            timestamp=result[4],
                        ),
                        result[3],
                    )
                    for result in results
                ]

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

        results = await self.get_nearest_matches_async(
            collection_name=collection_name,
            embedding=embedding,
            limit=1,
            min_relevance_score=min_relevance_score,
            with_embeddings=with_embedding,
        )
        if len(results) == 0:
            raise Exception("No match found")
        return results[0]

    async def __does_collection_exist_async(
        self, cur: Cursor, collection_name: str
    ) -> bool:
        results = await self.__get_collections_async(cur)
        return collection_name in results

    async def __get_collections_async(self, cur: Cursor) -> List[str]:
        cur.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
            """,
            (self._schema,),
        )
        return [row[0] for row in cur.fetchall()]

    def _check_dimensionality(self, dimension_num):
        if dimension_num > MAX_DIMENSIONALITY:
            raise ValueError(
                f"Dimensionality of {dimension_num} exceeds "
                + f"the maximum allowed value of {MAX_DIMENSIONALITY}."
            )
        if dimension_num <= 0:
            raise ValueError("Dimensionality must be a positive integer. ")

    def __serialize_metadata(self, record: MemoryRecord) -> str:
        return json.dumps(
            {
                "text": record._text,
                "description": record._description,
                "additional_metadata": record._additional_metadata,
            }
        )
