import os
from typing import List, Tuple

import numpy
from numpy import ndarray
from pgvector.psycopg import register_vector_async
from psycopg import AsyncCursor
from psycopg_pool import AsyncConnectionPool

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
    _connection_pool: AsyncConnectionPool

    def __init__(self, connection_string: str, min_pool: int, max_pool: int) -> None:
        self._connection_string = connection_string
        self._connection_pool = AsyncConnectionPool(
            self._connection_string, min_size=min_pool, max_size=max_pool
        )

    async def create_collection_async(
        self, collection_name: str, dimension_num: int
    ) -> None:
        async with self._connection_pool.connection() as conn:
            await register_vector_async(conn)
            async with conn.cursor() as cur:
                await cur.execute("CREATE SCHEMA IF NOT EXISTS %s", (collection_name,))
                await cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS %s.%s (
                        key TEXT PRIMARY KEY,
                        embedding VECTOR(%s),
                        metadata TEXT,
                        timestamp TIMESTAMP
                    )""",
                    (collection_name, MEMORY_TABLE_NAME, dimension_num),
                )

    async def get_collections_async(self) -> List[str]:
        async with self._connection_pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT schema_name FROM information_schema.schemata")
                return [row[0] for row in await cur.fetchall()]

    async def delete_collection_async(self, collection_name: str) -> None:
        async with self._connection_pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DROP SCHEMA IF EXISTS %s CASCADE", (collection_name,)
                )

    async def does_collection_exist_async(self, collection_name: str) -> bool:
        async with self._connection_pool.connection() as conn:
            async with conn.cursor() as cur:
                return await self.__does_collection_exist_async(collection_name, cur)

    async def upsert_async(self, collection_name: str, record: MemoryRecord) -> str:
        async with self._connection_pool.connection() as conn:
            async with conn.cursor() as cur:
                if not await self.__does_collection_exist_async(collection_name, cur):
                    raise Exception(f"Collection '{collection_name}' does not exist")
                await cur.execute(
                    """
                    INSERT INTO %s.%s (key, embedding, metadata, timestamp)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (key) DO UPDATE
                    SET embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata,
                        timestamp = EXCLUDED.timestamp
                    RETURNING key""",
                    (
                        collection_name,
                        MEMORY_TABLE_NAME,
                        record._id,
                        record.embedding,
                        record._text,
                        record._timestamp,
                    ),
                )
                result = await cur.fetchone()
                if result is None:
                    raise Exception("Upsert failed")
                return result[0]

    async def upsert_batch_async(
        self, collection_name: str, records: List[MemoryRecord]
    ) -> List[str]:
        async with self._connection_pool.connection() as conn:
            async with conn.cursor() as cur:
                if not await self.__does_collection_exist_async(collection_name, cur):
                    raise Exception(f"Collection '{collection_name}' does not exist")
                cur.nextset()
                await cur.executemany(
                    """
                    INSERT INTO %s.%s (key, embedding, metadata, timestamp)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (key) DO UPDATE
                    SET embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata,
                        timestamp = EXCLUDED.timestamp
                    RETURNING key""",
                    [
                        (
                            collection_name,
                            MEMORY_TABLE_NAME,
                            record._id,
                            record.embedding,
                            record._text,
                            record._timestamp,
                        )
                        for record in records
                    ],
                    returning=True,
                )

                # collate results
                results = [await cur.fetchone()]
                while cur.nextset():
                    results.append(await cur.fetchone())
                results.append(await cur.fetchone())
                if None in results:
                    raise Exception("Upsert failed")
                return [result[0] for result in results if result is not None]

    async def get_async(
        self, collection_name: str, key: str, with_embedding: bool
    ) -> MemoryRecord:
        async with self._connection_pool.connection() as conn:
            async with conn.cursor() as cur:
                if not await self.__does_collection_exist_async(collection_name, cur):
                    raise Exception(f"Collection '{collection_name}' does not exist")
                await cur.execute(
                    """
                    SELECT key, embedding, metadata
                    FROM %s.%s
                    WHERE key = %s""",
                    (collection_name, MEMORY_TABLE_NAME, key),
                )
                result = await cur.fetchone()
                if result is None:
                    raise Exception("Key not found")
                return MemoryRecord(
                    id=result[0],
                    embedding=result[1] if with_embedding else numpy.array([]),
                    text=result[2],
                    description="",
                    is_reference=False,
                    external_source_name=PostgresMemoryStore.__name__,
                )

    async def get_batch_async(
        self, collection_name: str, keys: List[str], with_embedding: bool
    ) -> List[MemoryRecord]:
        async with self._connection_pool.connection() as conn:
            async with conn.cursor() as cur:
                if not await self.__does_collection_exist_async(collection_name, cur):
                    raise Exception(f"Collection '{collection_name}' does not exist")
                await cur.execute(
                    """
                    SELECT key, embedding, metadata
                    FROM %s.%s
                    WHERE key = ANY(%s)""",
                    (collection_name, MEMORY_TABLE_NAME, keys),
                )
                results = await cur.fetchall()
                if len(results) == 0:
                    raise Exception("Keys not found")
                if len(results) != len(keys):
                    raise Exception("Some keys not found")
                return [
                    MemoryRecord(
                        id=result[0],
                        embedding=result[1] if with_embedding else numpy.array([]),
                        text=result[2],
                        description="",
                        is_reference=False,
                        external_source_name=PostgresMemoryStore.__name__,
                    )
                    for result in results
                ]

    async def remove_async(self, collection_name: str, key: str) -> None:
        async with self._connection_pool.connection() as conn:
            async with conn.cursor() as cur:
                if not await self.__does_collection_exist_async(collection_name, cur):
                    raise Exception(f"Collection '{collection_name}' does not exist")
                await cur.execute(
                    """
                    DELETE FROM %s.%s
                    WHERE key = %s""",
                    (collection_name, MEMORY_TABLE_NAME, key),
                )

    async def remove_batch_async(self, collection_name: str, keys: List[str]) -> None:
        async with self._connection_pool.connection() as conn:
            async with conn.cursor() as cur:
                if not await self.__does_collection_exist_async(collection_name, cur):
                    raise Exception(f"Collection '{collection_name}' does not exist")
                await cur.execute(
                    """
                    DELETE FROM %s.%s
                    WHERE key = ANY(%s)""",
                    (collection_name, MEMORY_TABLE_NAME, keys),
                )

    async def get_nearest_matches_async(
        self,
        collection_name: str,
        embedding: ndarray,
        limit: int,
        min_relevance_score: float,
        with_embeddings: bool,
    ) -> List[Tuple[MemoryRecord, float]]:
        async with self._connection_pool.connection() as conn:
            async with conn.cursor() as cur:
                if not await self.__does_collection_exist_async(collection_name, cur):
                    raise Exception(f"Collection '{collection_name}' does not exist")
                await cur.execute(
                    """
                    SELECT key, embedding, metadata, cosine_similarity
                    FROM(
                        SELECT key, embedding, metadata, 1 - (embedding <=> %s) AS cosine_similarity
                        FROM %s.%s
                    )
                    WHERE cosine_similarity >= %s
                    ORDER BY cosine_similarity DESC
                    LIMIT %s""",
                    (
                        embedding,
                        collection_name,
                        MEMORY_TABLE_NAME,
                        min_relevance_score,
                        limit,
                    ),
                )
                results = await cur.fetchall()
                return [
                    (
                        MemoryRecord(
                            id=result[0],
                            embedding=result[1] if with_embeddings else numpy.array([]),
                            text=result[2],
                            description="",
                            is_reference=False,
                            external_source_name=PostgresMemoryStore.__name__,
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
        async with self._connection_pool.connection() as conn:
            async with conn.cursor() as cur:
                if not await self.__does_collection_exist_async(collection_name, cur):
                    raise Exception(f"Collection '{collection_name}' does not exist")
                await cur.execute(
                    """
                    SELECT key, embedding, metadata, cosine_similarity
                    FROM(
                        SELECT key, embedding, metadata, 1 - (embedding <=> %s) AS cosine_similarity
                        FROM %s.%s
                    )
                    WHERE cosine_similarity >= %s
                    ORDER BY cosine_similarity DESC
                    LIMIT 1""",
                    (
                        embedding,
                        collection_name,
                        MEMORY_TABLE_NAME,
                        min_relevance_score,
                    ),
                )
                result = await cur.fetchone()
                if result is None:
                    raise Exception("No match found")
                return (
                    MemoryRecord(
                        id=result[0],
                        embedding=result[1] if with_embedding else numpy.array([]),
                        text=result[2],
                        description="",
                        is_reference=False,
                        external_source_name=PostgresMemoryStore.__name__,
                    ),
                    result[3],
                )

    async def __does_collection_exist_async(
        self, collection_name: str, cursor: AsyncCursor
    ) -> bool:
        async with self._connection_pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT schema_name
                    FROM information_schema.schemata
                    WHERE schema_name = %s""",
                    (collection_name,),
                )
                return await cur.fetchone() is not None
