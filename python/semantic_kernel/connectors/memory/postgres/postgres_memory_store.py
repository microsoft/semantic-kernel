# Copyright (c) Microsoft. All rights reserved.

import atexit
import json
import logging

import numpy as np
from numpy import ndarray
from psycopg import Cursor
from psycopg.sql import SQL, Identifier
from psycopg_pool import ConnectionPool
from pydantic import ValidationError

from semantic_kernel.connectors.memory.postgres.constants import DEFAULT_SCHEMA, MAX_DIMENSIONALITY
from semantic_kernel.connectors.memory.postgres.postgres_settings import PostgresSettings
from semantic_kernel.exceptions import (
    ServiceInitializationError,
    ServiceResourceNotFoundError,
    ServiceResponseException,
)
from semantic_kernel.exceptions.memory_connector_exceptions import MemoryConnectorInitializationError
from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.utils.feature_stage_decorator import experimental

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class PostgresMemoryStore(MemoryStoreBase):
    """A memory store that uses Postgres with pgvector as the backend."""

    _connection_string: str
    _connection_pool: ConnectionPool
    _default_dimensionality: int
    _schema: str

    def __init__(
        self,
        connection_string: str,
        default_dimensionality: int,
        min_pool: int | None = None,
        max_pool: int | None = None,
        schema: str = DEFAULT_SCHEMA,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ) -> None:
        """Initializes a new instance of the PostgresMemoryStore class.

        Args:
            connection_string: The connection string to the Postgres database.
            default_dimensionality: The default dimensionality of the embeddings.
            min_pool: The minimum number of connections in the connection pool.
            max_pool: The maximum number of connections in the connection pool.
            schema: The schema to use. (default: {"public"})
            env_file_path: Use the environment settings file as a fallback
                to environment variables. (Optional)
            env_file_encoding: The encoding of the environment settings file.
        """
        try:
            postgres_settings = PostgresSettings(
                connection_string=connection_string,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise MemoryConnectorInitializationError("Failed to create Postgres settings.", ex) from ex

        min_pool = min_pool or postgres_settings.min_pool
        max_pool = max_pool or postgres_settings.max_pool

        self._check_dimensionality(default_dimensionality)

        self._default_dimensionality = default_dimensionality
        self._connection_pool = ConnectionPool(
            min_size=min_pool, max_size=max_pool, open=True, kwargs=postgres_settings.get_connection_args()
        )
        self._schema = schema
        atexit.register(self._connection_pool.close)

    async def create_collection(
        self,
        collection_name: str,
        dimension_num: int | None = None,
    ) -> None:
        r"""Creates a new collection.

        Args:
            collection_name: The name of the collection to create.\n
            dimension_num: The dimensionality of the embeddings. (default: {None})
            Uses the default dimensionality when not provided

        Returns:
            None
        """
        if dimension_num is None:
            dimension_num = self._default_dimensionality
        else:
            self._check_dimensionality(dimension_num)

        with self._connection_pool.connection() as conn, conn.cursor() as cur:
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

    async def get_collections(self) -> list[str]:
        """Gets the list of collections.

        Returns:
            The list of collections.
        """
        with self._connection_pool.connection() as conn, conn.cursor() as cur:
            return await self.__get_collections(cur)

    async def delete_collection(self, collection_name: str) -> None:
        """Deletes a collection.

        Args:
            collection_name (str): The name of the collection to delete.

        Returns:
            None
        """
        with self._connection_pool.connection() as conn, conn.cursor() as cur:
            cur.execute(
                SQL("DROP TABLE IF EXISTS {scm}.{tbl} CASCADE").format(
                    scm=Identifier(self._schema), tbl=Identifier(collection_name)
                ),
            )

    async def does_collection_exist(self, collection_name: str) -> bool:
        """Checks if a collection exists.

        Args:
            collection_name: The name of the collection to check.

        Returns:
            True if the collection exists; otherwise, False.
        """
        with self._connection_pool.connection() as conn, conn.cursor() as cur:
            return await self.__does_collection_exist(cur, collection_name)

    async def upsert(self, collection_name: str, record: MemoryRecord) -> str:
        """Upserts a record.

        Args:
            collection_name: The name of the collection to upsert the record into.
            record: The record to upsert.

        Returns:
            The unique database key of the record. In Pinecone, this is the record ID.
        """
        with self._connection_pool.connection() as conn, conn.cursor() as cur:
            if not await self.__does_collection_exist(cur, collection_name):
                raise ServiceResourceNotFoundError(f"Collection '{collection_name}' does not exist")
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
                raise ServiceResponseException("Upsert failed")
            return result[0]

    async def upsert_batch(self, collection_name: str, records: list[MemoryRecord]) -> list[str]:
        """Upserts a batch of records.

        Args:
            collection_name: The name of the collection to upsert the records into.
            records: The records to upsert.

        Returns:
            List[str]: The unique database keys of the records.
        """
        with self._connection_pool.connection() as conn, conn.cursor() as cur:
            if not await self.__does_collection_exist(cur, collection_name):
                raise ServiceResourceNotFoundError(f"Collection '{collection_name}' does not exist")
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
                raise ServiceResponseException("Upsert failed")
            return [result[0] for result in results if result is not None]

    async def get(self, collection_name: str, key: str, with_embedding: bool = False) -> MemoryRecord:
        """Gets a record.

        Args:
            collection_name: The name of the collection to get the record from.
            key: The unique database key of the record.
            with_embedding: Whether to include the embedding in the result. (default: {False})

        Returns:
            The record.
        """
        with self._connection_pool.connection() as conn, conn.cursor() as cur:
            if not await self.__does_collection_exist(cur, collection_name):
                raise ServiceResourceNotFoundError(f"Collection '{collection_name}' does not exist")
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
                raise ServiceResourceNotFoundError("Key not found")
            return MemoryRecord.local_record(
                id=result[0],
                embedding=(
                    np.fromstring(result[1].strip("[]"), dtype=float, sep=",") if with_embedding else np.array([])
                ),
                text=result[2]["text"],
                description=result[2]["description"],
                additional_metadata=result[2]["additional_metadata"],
                timestamp=result[3],
            )

    async def get_batch(
        self, collection_name: str, keys: list[str], with_embeddings: bool = False
    ) -> list[MemoryRecord]:
        """Gets a batch of records.

        Args:
            collection_name: The name of the collection to get the records from.
            keys: The unique database keys of the records.
            with_embeddings: Whether to include the embeddings in the results. (default: {False})

        Returns:
            The records that were found from list of keys, can be empty.
        """
        with self._connection_pool.connection() as conn, conn.cursor() as cur:
            if not await self.__does_collection_exist(cur, collection_name):
                raise ServiceResourceNotFoundError(f"Collection '{collection_name}' does not exist")
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
                    embedding=(
                        np.fromstring(result[1].strip("[]"), dtype=float, sep=",") if with_embeddings else np.array([])
                    ),
                    text=result[2]["text"],
                    description=result[2]["description"],
                    additional_metadata=result[2]["additional_metadata"],
                    timestamp=result[3],
                )
                for result in results
            ]

    async def remove(self, collection_name: str, key: str) -> None:
        """Removes a record.

        Args:
            collection_name: The name of the collection to remove the record from.
            key: The unique database key of the record to remove.

        Returns:
            None
        """
        with self._connection_pool.connection() as conn, conn.cursor() as cur:
            if not await self.__does_collection_exist(cur, collection_name):
                raise ServiceResourceNotFoundError(f"Collection '{collection_name}' does not exist")
            cur.execute(
                SQL(
                    """
                        DELETE FROM {scm}.{tbl}
                        WHERE key = %s
                        """
                ).format(scm=Identifier(self._schema), tbl=Identifier(collection_name)),
                (key,),
            )

    async def remove_batch(self, collection_name: str, keys: list[str]) -> None:
        """Removes a batch of records.

        Args:
            collection_name: The name of the collection to remove the records from.
            keys: The unique database keys of the records to remove.

        Returns:
            None
        """
        with self._connection_pool.connection() as conn, conn.cursor() as cur:
            if not await self.__does_collection_exist(cur, collection_name):
                raise ServiceResourceNotFoundError(f"Collection '{collection_name}' does not exist")
            cur.execute(
                SQL(
                    """
                        DELETE FROM {scm}.{tbl}
                        WHERE key = ANY(%s)
                        """
                ).format(scm=Identifier(self._schema), tbl=Identifier(collection_name)),
                (list(keys),),
            )

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
            collection_name: The name of the collection to get the nearest matches from.
            embedding: The embedding to find the nearest matches to.
            limit: The maximum number of matches to return.
            min_relevance_score: The minimum relevance score of the matches. (default: {0.0})
            with_embeddings: Whether to include the embeddings in the results. (default: {False})

        Returns:
            The records and their relevance scores.
        """
        with self._connection_pool.connection() as conn, conn.cursor() as cur:
            if not await self.__does_collection_exist(cur, collection_name):
                raise ServiceResourceNotFoundError(f"Collection '{collection_name}' does not exist")
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
                        embedding=(
                            np.fromstring(result[1].strip("[]"), dtype=float, sep=",")
                            if with_embeddings
                            else np.array([])
                        ),
                        text=result[2]["text"],
                        description=result[2]["description"],
                        additional_metadata=result[2]["additional_metadata"],
                        timestamp=result[4],
                    ),
                    result[3],
                )
                for result in results
            ]

    async def get_nearest_match(
        self,
        collection_name: str,
        embedding: ndarray,
        min_relevance_score: float = 0.0,
        with_embedding: bool = False,
    ) -> tuple[MemoryRecord, float]:
        """Gets the nearest match to an embedding using cosine similarity.

        Args:
            collection_name: The name of the collection to get the nearest match from.
            embedding: The embedding to find the nearest match to.
            min_relevance_score: The minimum relevance score of the match. (default: {0.0})
            with_embedding: Whether to include the embedding in the result. (default: {False})

        Returns:
            Tuple[MemoryRecord, float]: The record and the relevance score.
        """
        results = await self.get_nearest_matches(
            collection_name=collection_name,
            embedding=embedding,
            limit=1,
            min_relevance_score=min_relevance_score,
            with_embeddings=with_embedding,
        )
        if len(results) == 0:
            raise ServiceResourceNotFoundError("No match found")
        return results[0]

    async def __does_collection_exist(self, cur: Cursor, collection_name: str) -> bool:
        results = await self.__get_collections(cur)
        return collection_name in results

    async def __get_collections(self, cur: Cursor) -> list[str]:
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
            raise ServiceInitializationError(
                f"Dimensionality of {dimension_num} exceeds " + f"the maximum allowed value of {MAX_DIMENSIONALITY}."
            )
        if dimension_num <= 0:
            raise ServiceInitializationError("Dimensionality must be a positive integer. ")

    def __serialize_metadata(self, record: MemoryRecord) -> str:
        return json.dumps({
            "text": record._text,
            "description": record._description,
            "additional_metadata": record._additional_metadata,
        })

    # Enable the connection pool to be closed when using as a context manager
    def __enter__(self) -> "PostgresMemoryStore":
        """Enter the runtime context."""
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        """Exit the runtime context and dispose of the connection pool."""
        self._connection_pool.close()
        return False
