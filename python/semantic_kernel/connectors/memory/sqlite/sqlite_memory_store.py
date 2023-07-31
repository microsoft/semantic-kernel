import aiosqlite as sqlite

from logging import Logger
from typing import List, Optional, Tuple

import numpy as np

from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.utils.null_logger import NullLogger
from semantic_kernel.connectors.memory.sqlite.utils import (
    deserialize_metadata,
    deserialize_embedding,
    deserialize_timestamp,
    serialize_timestamp,
    Metadata,
)

TABLE_NAME = "SKMemoryTable"


class SQLiteMemoryStore(MemoryStoreBase):
    """A memory store that uses SQLite as the backend."""

    _filepath: str
    _conn: sqlite.Connection

    def __init__(self, filepath: str) -> None:
        super().__init__()
        self._filepath = filepath
        self._conn = sqlite.connect(filepath)

    async def __aenter__(self):
        await self.create_table_if_not_exists_async()

    async def close_async(self):
        await self._conn.close()

    @staticmethod
    async def connect_async(filepath: str):
        store = SQLiteMemoryStore(filepath)
        await store.create_table_if_not_exists_async()
        return store

    async def create_table_if_not_exists_async(self) -> None:
        async with self._conn.execute(
            f"""CREATE TABLE IF NOT EXISTS {TABLE_NAME}(
                collection TEXT,
                key TEXT,
                metadata TEXT,
                embedding TEXT,
                timestamp TEXT,
                PRIMARY KEY(collection, key))"""
        ):
            return

    async def create_collection_async(self, collection_name: str) -> None:
        async with await self._conn.execute_insert(
            f"""
            INSERT INTO {TABLE_NAME}(collection)
            VALUES(?);
            """,
            [collection_name],
        ) as cursor:
            await cursor.commit()

    async def does_collection_exist_async(self, collection_name: str) -> bool:
        async with self._conn.execute_fetchall(
            f"""
                SELECT DISTINCT(collection)
                FROM {TABLE_NAME}
                WHERE collection = ?;";
            """,
            [collection_name],
        ) as rows:
            return bool(rows)

    async def get_collections_async(self) -> List[str]:
        async with self._conn.execute_fetchall(
            f"""
                SELECT DISTINCT(collection)
                FROM {TABLE_NAME}";
            """
        ) as rows:
            return list(map(lambda r: r["collection"], rows))

    async def delete_collection_async(self, collection_name: str):
        async with self._conn.execute(
            f"""
                DELETE FROM {TABLE_NAME}
                WHERE collection = ?;
            """,
            [collection_name],
        ) as cursor:
            await cursor.commit()

    async def _update_batch_async(
        self,
        collection: str,
        records: List[MemoryRecord],
    ):
        async with self._conn.executemany(
            f"""
                UPDATE {TABLE_NAME}
                SET metadata = ?, embedding = ?, timestamp = ?
                WHERE collection = ? AND key = ?;
            """,
            map(
                lambda r: (
                    Metadata.from_memory_record(r).to_json(),
                    r.embedding,
                    serialize_timestamp(r._timestamp),
                    collection,
                    r._id,
                ),
                records,
            ),
        ) as cursor:
            await cursor.commit()

    async def _insert_or_ignore_batch_async(
        self, collection: str, records: List[MemoryRecord]
    ):
        async with self._conn.executemany(
            f"""
                INSERT OR IGNORE INTO {TABLE_NAME}(collection, key, metadata, embedding, timestamp)
                VALUES(?, ?, ?, ?, ?);
            """,
            map(
                lambda r: (
                    collection,
                    r._id,
                    Metadata.from_memory_record(r).to_json(),
                    r.embedding,
                    serialize_timestamp(r._timestamp),
                ),
                records,
            ),
        ) as cursor:
            await cursor.commit()

    async def upsert_async(self, collection_name: str, record: MemoryRecord) -> str:
        await self._update_batch_async(
            collection=collection_name,
            records=[record],
        )

        await self._insert_or_ignore_batch_async(
            collection=collection_name,
            records=[record],
        )

        return record._id

    async def upsert_batch_async(
        self, collection_name: str, records: List[MemoryRecord]
    ) -> List[str]:
        await self._update_batch_async(
            collection=collection_name,
            records=records,
        )

        await self._insert_or_ignore_batch_async(
            collection=collection_name,
            records=records,
        )

        return map(lambda r: r._id, records)

    async def get_async(
        self, collection_name: str, key: str, with_embedding: bool
    ) -> MemoryRecord:
        async with self._conn.execute(
            f"""
                SELECT metadata, embedding, timestamp FROM {TABLE_NAME} WHERE collection=? and key=?
            """,
            (collection_name, key),
        ) as cursor:
            record = await cursor.fetchone()
            if not record:
                raise Exception(
                    f"Collection[{collection_name}] or Key[{key}] not found"
                )

            metadata = deserialize_metadata(record["metadata"])

            return MemoryRecord.local_record(
                id=key,
                text=metadata["text"] or "",
                description=metadata["description"],
                additional_metadata=metadata["additional_metadata"],
                embedding=deserialize_embedding(record["embedding"])
                if with_embedding
                else None,
                timestamp=deserialize_timestamp(record["timestamp"]),
            )

    async def get_batch_async(
        self, collection_name: str, keys: List[str], with_embeddings: bool
    ) -> List[MemoryRecord]:
        async with self._conn.execute_fetchall(
            f"""
                SELECT key, metadata, embedding, timestamp FROM {TABLE_NAME} WHERE collection=? and key in (%s)
            """
            % ", ".join("?" * len(keys)),
            (collection_name, *keys),
        ) as rows:
            return [
                MemoryRecord.local_record(
                    id=row["key"],
                    text=metadata["text"] or "",
                    description=metadata["description"],
                    additional_metadata=metadata["additional_metadata"],
                    embedding=deserialize_embedding(row["embedding"])
                    if with_embeddings
                    else None,
                )
                for row in rows
                if (metadata := deserialize_metadata(row["metadata"]) is not None)
            ]

    async def remove_batch_async(self, collection_name: str, keys: List[str]) -> None:
        async with self._conn.execute(
            f"""
                DELETE FROM {TABLE_NAME} WHERE collection=? and key in (%s)
            """
            % ", ".join("?" * len(keys)),
            (collection_name, *keys),
        ) as cursor:
            await cursor.commit()

    async def remove_async(self, collection_name: str, key: str) -> None:
        await self.remove_batch_async(collection_name, [key])

    async def get_nearest_matches_async(
        self,
        collection_name: str,
        embedding: ndarray,
        limit: int,
        min_relevance_score: float,
        with_embeddings: bool,
    ) -> List[Tuple[MemoryRecord, float]]:
        async with self._conn.execute_fetchall(
            f"""
                SELECT key, metadata, embedding, timestamp FROM {TABLE_NAME} WHERE collection=? ORDER BY relevance_score DESC LIMIT ?
            """,
            (collection_name, limit),
        ) as rows:
            return [
                (
                    MemoryRecord.local_record(
                        id=row["key"],
                        text=metadata["text"] or "",
                        description=metadata["description"],
                        additional_metadata=metadata["additional_metadata"],
                        embedding=deserialize_embedding(row["embedding"])
                        if with_embeddings
                        else None,
                    ),
                    row["relevance_score"],
                )
                for row in rows
                if (metadata := deserialize_metadata(row["metadata"]) is not None)
            ]
