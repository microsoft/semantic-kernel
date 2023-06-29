# Copyright (c) Microsoft. All rights reserved.

import atexit
import json
import os
from typing import List, Tuple

import numpy
from numpy import ndarray
from psycopg import Cursor
from psycopg_pool import ConnectionPool

from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase

# On Windows, Psycopg is not compatible with the default ProactorEventLoop.
# Please use a different loop, for instance the SelectorEventLoop.
# https://www.psycopg.org/psycopg3/docs/advanced/async.html
if os.name == "nt":
    import asyncio

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

MEMORY_TABLE_NAME = "sk_memory_table"


class PostgresMemoryStore(MemoryStoreBase):
    _connection_string: str
    _connection_pool: ConnectionPool

    def __init__(self, connection_string: str, min_pool: int, max_pool: int) -> None:
        self._connection_string = connection_string
        self._connection_pool = ConnectionPool(
            self._connection_string, min_size=min_pool, max_size=max_pool
        )
        atexit.register(self._connection_pool.close)

    async def create_collection_async(
        self, collection_name: str, dimension_num: int
    ) -> None:
        with self._connection_pool.connection() as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            with conn.cursor() as cur:
                cur.execute(f"CREATE SCHEMA IF NOT EXISTS {collection_name}")
                cur.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {collection_name}.{MEMORY_TABLE_NAME} (
                        key TEXT PRIMARY KEY,
                        embedding vector({dimension_num}),
                        metadata TEXT,
                        timestamp TIMESTAMP
                    )""",
                )

    async def get_collections_async(self) -> List[str]:
        with self._connection_pool.connection() as conn:
            with conn.cursor() as cur:
                return await self.__get_collections_async(cur)

    async def delete_collection_async(self, collection_name: str) -> None:
        with self._connection_pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"DROP SCHEMA IF EXISTS {collection_name} CASCADE",
                )

    async def does_collection_exist_async(self, collection_name: str) -> bool:
        with self._connection_pool.connection() as conn:
            with conn.cursor() as cur:
                return await self.__does_collection_exist_async(cur, collection_name)

    async def upsert_async(self, collection_name: str, record: MemoryRecord) -> str:
        with self._connection_pool.connection() as conn:
            with conn.cursor() as cur:
                if not self.__does_collection_exist_async(cur, collection_name):
                    raise Exception(f"Collection '{collection_name}' does not exist")
                cur.execute(
                    f"""
                    INSERT INTO {collection_name}.{MEMORY_TABLE_NAME} (key, embedding, metadata, timestamp)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (key) DO UPDATE
                    SET embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata,
                        timestamp = EXCLUDED.timestamp
                    RETURNING key""",
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
        with self._connection_pool.connection() as conn:
            with conn.cursor() as cur:
                if not self.__does_collection_exist_async(cur, collection_name):
                    raise Exception(f"Collection '{collection_name}' does not exist")
                cur.nextset()
                cur.executemany(
                    f"""
                    INSERT INTO {collection_name}.{MEMORY_TABLE_NAME} (key, embedding, metadata, timestamp)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (key) DO UPDATE
                    SET embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata,
                        timestamp = EXCLUDED.timestamp
                    RETURNING key""",
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
        self, collection_name: str, key: str, with_embedding: bool
    ) -> MemoryRecord:
        with self._connection_pool.connection() as conn:
            with conn.cursor() as cur:
                if not self.__does_collection_exist_async(cur, collection_name):
                    raise Exception(f"Collection '{collection_name}' does not exist")
                cur.execute(
                    f"""
                    SELECT key, embedding, metadata
                    FROM {collection_name}.{MEMORY_TABLE_NAME}
                    WHERE key = %s""",
                    (key,),
                )
                result = cur.fetchone()
                if result is None:
                    raise KeyError("Key not found")
                return self.__deserialize_metadata(
                    MemoryRecord(
                        id=result[0],
                        embedding=result[1] if with_embedding else numpy.array([]),
                        text=None,
                        description=None,
                        additional_metadata=None,
                        is_reference=False,
                        external_source_name=PostgresMemoryStore.__name__,
                    ),
                    result[2],
                )

    async def get_batch_async(
        self, collection_name: str, keys: List[str], with_embeddings: bool
    ) -> List[MemoryRecord]:
        with self._connection_pool.connection() as conn:
            with conn.cursor() as cur:
                if not self.__does_collection_exist_async(cur, collection_name):
                    raise Exception(f"Collection '{collection_name}' does not exist")
                cur.execute(
                    f"""
                    SELECT key, embedding, metadata
                    FROM {collection_name}.{MEMORY_TABLE_NAME}
                    WHERE key = ANY(%s)""",
                    (list(keys),),
                )
                results = cur.fetchall()
                if len(results) == 0:
                    raise KeyError("Keys not found")
                if len(results) != len(keys):
                    raise KeyError("Some keys not found")
                return [
                    self.__deserialize_metadata(
                        MemoryRecord(
                            id=result[0],
                            embedding=result[1] if with_embeddings else numpy.array([]),
                            text=None,
                            description=None,
                            additional_metadata=None,
                            is_reference=False,
                            external_source_name=PostgresMemoryStore.__name__,
                        ),
                        result[2],
                    )
                    for result in results
                ]

    async def remove_async(self, collection_name: str, key: str) -> None:
        with self._connection_pool.connection() as conn:
            with conn.cursor() as cur:
                if not self.__does_collection_exist_async(cur, collection_name):
                    raise Exception(f"Collection '{collection_name}' does not exist")
                cur.execute(
                    f"""
                    DELETE FROM {collection_name}.{MEMORY_TABLE_NAME}
                    WHERE key = %s""",
                    (key,),
                )

    async def remove_batch_async(self, collection_name: str, keys: List[str]) -> None:
        with self._connection_pool.connection() as conn:
            with conn.cursor() as cur:
                if not self.__does_collection_exist_async(cur, collection_name):
                    raise Exception(f"Collection '{collection_name}' does not exist")
                cur.execute(
                    f"""
                    DELETE FROM {collection_name}.{MEMORY_TABLE_NAME}
                    WHERE key = ANY(%s)""",
                    (list(keys),),
                )

    async def get_nearest_matches_async(
        self,
        collection_name: str,
        embedding: ndarray,
        limit: int,
        min_relevance_score: float,
        with_embeddings: bool,
    ) -> List[Tuple[MemoryRecord, float]]:
        with self._connection_pool.connection() as conn:
            with conn.cursor() as cur:
                if not self.__does_collection_exist_async(cur, collection_name):
                    raise Exception(f"Collection '{collection_name}' does not exist")
                cur.execute(
                    f"""
                    SELECT key, embedding, metadata, cosine_similarity
                    FROM (
                        SELECT key, embedding, metadata, 1 - (embedding <=> '{embedding.tolist()}') AS cosine_similarity
                        FROM {collection_name}.{MEMORY_TABLE_NAME}
                    ) AS subquery
                    WHERE cosine_similarity >= {min_relevance_score}
                    ORDER BY cosine_similarity DESC
                    LIMIT {limit}""",
                )
                results = cur.fetchall()

                return [
                    (
                        self.__deserialize_metadata(
                            MemoryRecord(
                                id=result[0],
                                embedding=result[1]
                                if with_embeddings
                                else numpy.array([]),
                                text=None,
                                description=None,
                                additional_metadata=None,
                                is_reference=False,
                                external_source_name=PostgresMemoryStore.__name__,
                            ),
                            result[2],
                        ),
                        result[3],
                    )
                    for result in results
                ]

    async def get_nearest_match_async(
        self,
        collection_name: str,
        embedding: ndarray,
        min_relevance_score: float,
        with_embedding: bool,
    ) -> Tuple[MemoryRecord, float]:
        with self._connection_pool.connection() as conn:
            with conn.cursor() as cur:
                if not self.__does_collection_exist_async(cur, collection_name):
                    raise Exception(f"Collection '{collection_name}' does not exist")
                cur.execute(
                    f"""
                    SELECT key, embedding, metadata, cosine_similarity
                    FROM (
                        SELECT key, embedding, metadata, 1 - (embedding <=> '{embedding.tolist()}') AS cosine_similarity
                        FROM {collection_name}.{MEMORY_TABLE_NAME}
                    ) AS subquery
                    WHERE cosine_similarity >= {min_relevance_score}
                    ORDER BY cosine_similarity DESC
                    LIMIT 1""",
                )
                result = cur.fetchone()
                if result is None:
                    raise Exception("No match found")
                return (
                    self.__deserialize_metadata(
                        MemoryRecord(
                            id=result[0],
                            embedding=result[1] if with_embedding else numpy.array([]),
                            text=None,
                            description=None,
                            additional_metadata=None,
                            is_reference=False,
                            external_source_name=PostgresMemoryStore.__name__,
                        ),
                        result[2],
                    ),
                    result[3],
                )

    async def __does_collection_exist_async(
        self, cur: Cursor, collection_name: str
    ) -> bool:
        results = await self.__get_collections_async(cur)
        return collection_name in results

    async def __get_collections_async(self, cur: Cursor) -> List[str]:
        cur.execute("SELECT schema_name FROM information_schema.schemata")
        return [row[0] for row in cur.fetchall()]

    def __serialize_metadata(self, record: MemoryRecord) -> str:
        return json.dumps(
            {
                "text": record._text,
                "description": record._description,
                "additional_metadata": record._additional_metadata,
            }
        )

    def __deserialize_metadata(
        self, record: MemoryRecord, metadata: str
    ) -> MemoryRecord:
        metadata_dict: dict[str, str] = json.loads(metadata)
        record._text = metadata_dict["text"]
        record._description = metadata_dict["description"]
        record._additional_metadata = metadata_dict["additional_metadata"]
        return record
