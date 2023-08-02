import aiosqlite as sqlite

from logging import Logger
from typing import List, Optional, Tuple
import heapq

import numpy as np

from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.utils.null_logger import NullLogger
from semantic_kernel.connectors.memory.sqlite.utils import (
    deserialize_metadata,
    deserialize_embedding,
    deserialize_timestamp,
    serialize_timestamp,
    serialize_embedding,
    Metadata,
)

TABLE_NAME = "SKMemoryTable"


class SQLiteMemoryStore(MemoryStoreBase):
    """A memory store that uses SQLite as the backend."""

    _filepath: str
    _conn: sqlite.Connection
    _logger: Logger

    def __init__(self, filepath: str, logger: Optional[Logger]) -> None:
        """Initializes a new instance of the SQLiteMemoryStore class.

        Arguments:
            filepath {str}: The path to the SQLite database file.
            logger {Optional[Logger]} -- The logger to use. (default: {None})
        """
        super().__init__()
        self._filepath = filepath
        self._conn = sqlite.connect(filepath)
        self._logger = logger or NullLogger()

    async def __aenter__(self):
        self._logger.debug("Entering __aenter__")
        await self._create_table_if_not_exists_async()

    async def close_async(self):
        self._logger.debug("close_async called")
        await self._conn.close()

    @staticmethod
    async def connect_async(filepath: str):
        store = SQLiteMemoryStore(filepath)
        await store._create_table_if_not_exists_async()
        return store

    async def _create_table_if_not_exists_async(self) -> None:
        async with self._conn.execute(
            f"""CREATE TABLE IF NOT EXISTS {TABLE_NAME}(
                collection TEXT,
                key TEXT,
                metadata TEXT,
                embedding TEXT,
                timestamp TEXT,
                PRIMARY KEY(collection, key))"""
        ):
            self._conn.commit()
            return

    async def create_collection_async(self, collection_name: str) -> None:
        """Creates a new collection in the memory store.

        Arguments:
            collection_name {str} -- The name of the collection to create.

        Returns:
            None
        """
        async with self._conn.execute_insert(
            f"""
            INSERT INTO {TABLE_NAME}(collection)
            VALUES(?);
            """,
            [collection_name],
        ):
            self._logger.debug(
                f"collection {collection_name} created in Table {TABLE_NAME}"
            )
            await self._conn.commit()

    async def does_collection_exist_async(self, collection_name: str) -> bool:
        """Checks if a collection exists in the memory store.

        Arguments:
            collection_name {str} -- The name of the collection to check.

        Returns:
            bool -- True if the collection exists, False otherwise.
        """
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
        """Gets a list of all collections in the memory store.

        Returns:
            List[str] -- A list of all collections in the memory store.
        """
        async with self._conn.execute_fetchall(
            f"""
                SELECT DISTINCT(collection)
                FROM {TABLE_NAME}";
            """
        ) as rows:
            return list(map(lambda r: r["collection"], rows))

    async def delete_collection_async(self, collection_name: str):
        """Deletes a collection from the memory store.

        Arguments:
            collection_name {str} -- The name of the collection to delete.

        Returns:
            None
        """
        async with self._conn.execute(
            f"""
                DELETE FROM {TABLE_NAME}
                WHERE collection = ?;
            """,
            [collection_name],
        ):
            await self._conn.commit()

    async def upsert_batch_async(
        self, collection: str, records: List[MemoryRecord]
    ) -> List[str]:
        """Upserts a batch of records into the memory store.

        Arguments:
            collection {str} -- The name of the collection to upsert into.
            records {List[MemoryRecord]} -- The records to upsert.

        Returns:
            List[str] -- A list of keys for the upserted records.
        """
        with self._conn.executemany(
            f"""
                INSERT INTO {TABLE_NAME}(collection, key, metadata, embedding, timestamp)
                VALUES(?, ?, ?, ?, ?)
                ON CONFLICT(collection, key) DO UPDATE SET metadata = ?, embedding = ?, timestamp = ?
            """,
            map(
                lambda r: (
                    collection,
                    r._key,
                    Metadata.from_memory_record(r).to_json(),
                    serialize_embedding(r.embedding),
                    serialize_timestamp(r._timestamp),
                ),
                records,
            ),
        ):
            self._conn.commit()
            return [r._key for r in records]

    async def upsert_async(self, collection_name: str, record: MemoryRecord) -> str:
        """Upserts a single record into the memory store.

        Arguments:
            collection_name {str} -- The name of the collection to upsert into.
            record {MemoryRecord} -- The record to upsert.

        Returns:
            str -- The key for the upserted record.
        """
        keys = await self.upsert_batch_async(collection_name, [record])
        if len(keys) == 0:
            raise Exception("upsert failed")

        return keys[0]

    async def get_async(
        self, collection_name: str, key: str, with_embedding: bool
    ) -> MemoryRecord:
        """Gets a single record from the memory store.

        Arguments:
            collection_name {str} -- The name of the collection to get from.
            key {str} -- The key of the record to get.
            with_embedding {bool} -- Whether or not to include the embedding in the returned record.

        Returns:
            MemoryRecord -- The record.
        """
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
        """Gets a batch of records from the memory store.

        Arguments:
            collection_name {str} -- The name of the collection to get from.
            keys {List[str]} -- The keys of the records to get.
            with_embeddings {bool} -- Whether or not to include the embeddings in the returned records.

        Returns:
            List[MemoryRecord] -- The records.
        """
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
        ):
            await self._conn.commit()

    async def remove_async(self, collection_name: str, key: str) -> None:
        await self.remove_batch_async(collection_name, [key])

    async def get_nearest_matches_async(
        self,
        collection_name: str,
        embedding: np.ndarray,
        limit: int,
        min_relevance_score: float,
        with_embeddings: bool,
    ) -> List[Tuple[MemoryRecord, float]]:
        async with self._conn.execute_fetchall(
            f"""
                SELECT key, metadata, embedding, timestamp FROM {TABLE_NAME} WHERE collection=?
            """,
            (collection_name),
        ) as rows:
            min_heap = []
            for row in rows:
                vector = deserialize_embedding(row["embedding"])
                revelance = np.dot(vector, embedding)
                if revelance < min_relevance_score:
                    continue
                if with_embeddings:
                    row["embedding"] = vector
                if len(min_heap) == limit:
                    heapq.heappushpop(min_heap, (revelance, row))
                else:
                    heapq.heappush(min_heap, (revelance, row))

            result = []
            for relevance, row in min_heap:
                metadata = Metadata.from_json(row["metadata"])
                row["timestamp"] = deserialize_timestamp(row["timestamp"])
                result.append(
                    (
                        MemoryRecord.local_record(
                            id=row["key"],
                            text=metadata.text or "",
                            description=metadata["description"],
                            additional_metadata=row["additional_metadata"],
                            embedding=row["embedding"]  # we already deserialized it
                            if with_embeddings
                            else np.array([]),
                            timestamp=row["timestamp"],
                        ),
                        relevance,
                    )
                )

            result.sort(key=lambda x: x[1], reverse=True)
            return result

    async def get_nearest_match_async(
        self,
        collection_name: str,
        embedding: np.ndarray,
        min_relevance_score: float,
        with_embedding: bool,
    ) -> Tuple[MemoryRecord, float]:
        result = await self.get_nearest_matches_async(
            collection_name,
            embedding,
            limit=1,
            min_relevance_score=min_relevance_score,
            with_embeddings=with_embedding,
        )
        if len(result) == 0:
            raise Exception("No matches found")

        return result[0]
