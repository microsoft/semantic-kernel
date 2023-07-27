import aiosqlite as sqlite
from dataclasses import dataclass
from logging import Logger
from typing import List, Optional, Tuple

import numpy as np

from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.utils.null_logger import NullLogger

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
        await self._conn.execute(
            f"""CREATE TABLE IF NOT EXISTS {TABLE_NAME}(
                collection TEXT,
                key TEXT,
                metadata TEXT,
                embedding TEXT,
                timestamp TEXT,
                PRIMARY KEY(collection, key))"""
        )

    async def create_collection_async(self, collection_name: str) -> None:
        await self._conn.execute_insert(
            f"""
            INSERT INTO {TABLE_NAME}(collection)
            VALUES(?);
            """,
            collection_name,
        )

        await self._conn.commit()

    async def does_collection_exist_async(self, collection_name: str) -> bool:
        rows = await self._conn.execute_fetchall(
            f"""
                SELECT DISTINCT(collection)
                FROM {TABLE_NAME}
                WHERE collection = ?;";
            """,
            collection_name,
        )
        return bool(rows)

    async def get_collections_async(self) -> List[str]:
        rows = await self._conn.execute_fetchall(
            f"""
                SELECT DISTINCT(collection)
                FROM {TABLE_NAME}";
            """
        )
        return list(map(lambda r: r["collection"], rows))

    async def delete_collection_async(self, collection_name: str):
        await self._conn.execute(
            f"""
                DELETE FROM {TABLE_NAME}
                WHERE collection = ?;
            """,
            collection_name,
        )

        await self._conn.commit()

    async def _update_batch_async(
        self,
        collection: str,
        records: List[MemoryRecord],
    ):
        await self._conn.executemany(
            f"""
                UPDATE {TABLE_NAME}
                SET metadata = ?, embedding = ?, timestamp = ?
                WHERE collection = ? AND key = ?;
            """,
            map(
                lambda r: SQLiteMemoryStore.memory_record_to_tuple(collection, r),
                records,
            ),
        )

        await self._conn.commit()

    @staticmethod
    def memory_record_to_tuple(collection: str, record: MemoryRecord):  # type: ignore
        return (
            collection,
            record._id,  # Note: id field is key
            record._additional_metadata,
            record.embedding.tolist(),
            record._timestamp,
        )

    async def _insert_or_ignore_batch_async(
        self, collection: str, records: List[MemoryRecord]
    ):
        await self._conn.executemany(
            f"""
                INSERT OR IGNORE INTO {TABLE_NAME}(collection, key, metadata, embedding, timestamp)
                VALUES(?, ?, ?, ?, ?);
            """,
            map(
                lambda r: SQLiteMemoryStore.memory_record_to_tuple(collection, r),
                records,
            ),
        )
        await self._conn.commit()

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
