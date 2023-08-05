import heapq
from logging import Logger
from typing import List, Optional, Tuple

import aiosqlite as sqlite
import numpy as np

from semantic_kernel.connectors.memory.sqlite.utils import (
    Metadata,
    deserialize_embedding,
    deserialize_timestamp,
    serialize_embedding,
    serialize_timestamp,
)
from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.utils.null_logger import NullLogger

TABLE_NAME = "SKMemoryTable"


class SQLiteMemoryStore(MemoryStoreBase):
    """A memory store that uses SQLite as the backend."""

    _filepath: str
    _conn: Optional[sqlite.Connection]
    _logger: Logger

    def __init__(self, filepath: str, logger: Optional[Logger] = None) -> None:
        """Initializes a new instance of the SQLiteMemoryStore class. DB connection is not established until 
        connect() is called.

        Arguments:
            filepath {str}: The path to the SQLite database file.
            logger {Optional[Logger]} -- The logger to use. (default: {None})
        """
        super().__init__()
        self._filepath = filepath
        self._conn = None
        self._logger = logger or NullLogger()

    async def __aenter__(self):
        self._logger.debug("Entering __aenter__")
        await self.connect()
        await self._create_table_if_not_exists_async()
        return self

    async def __aexit__(self, *args):
        await self.close_async()

    async def close_async(self):
        self._logger.debug("close_async called")
        await self._conn.close()

    async def connect(self):
        self._conn = await sqlite.connect(self._filepath)

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
            await self._conn.commit()
            return

    async def create_collection_async(self, collection_name: str) -> None:
        """Creates a new collection in the memory store.

        Arguments:
            collection_name {str} -- The name of the collection to create.

        Returns:
            None
        """
        if await self.does_collection_exist_async(collection_name):
            return
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
                SELECT DISTINCT(collection) FROM {TABLE_NAME} WHERE collection = ?
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
                SELECT DISTINCT(collection) FROM {TABLE_NAME};
            """
        ) as rows:
            return list(map(lambda r: r[0], rows))

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
        async with self._conn.executemany(
            f"""
                INSERT INTO {TABLE_NAME}(collection, key, metadata, embedding, timestamp)
                VALUES(?, ?, ?, ?, ?)
                ON CONFLICT(collection, key) DO UPDATE SET metadata = excluded.metadata, 
                embedding = excluded.embedding, timestamp = excluded.timestamp;
            """,
            map(
                lambda r: (
                    collection,
                    r._id or r._key,
                    Metadata.from_memory_record(r).to_json(),
                    serialize_embedding(r.embedding),
                    serialize_timestamp(r._timestamp),
                ),
                records,
            ),
        ):
            await self._conn.commit()
            return [r._id or r._key for r in records]

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
        self, collection_name: str, key: str, with_embedding: bool = False
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
                raise KeyError(f"Collection[{collection_name}] or Key[{key}] not found")

            metadata = Metadata.from_json(record[0])

            return MemoryRecord.local_record(
                id=key,
                text=metadata.text,
                description=metadata.description,
                additional_metadata=metadata.additional_metadata,
                embedding=deserialize_embedding(record[1]) if with_embedding else None,
                timestamp=deserialize_timestamp(record[2]),
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
            result: List[MemoryRecord] = []
            for row in rows:
                metadata = Metadata.from_json(row[1])
                result.append(
                    MemoryRecord.local_record(
                        id=row[0],
                        text=metadata.text,
                        description=metadata.description,
                        additional_metadata=metadata.additional_metadata,
                        embedding=deserialize_embedding(row[2])
                        if with_embeddings
                        else None,
                        timestamp=deserialize_timestamp(row[3]),
                    )
                )

            return result

    async def remove_batch_async(self, collection_name: str, keys: List[str]) -> None:
        """Remove a batch of records identified by collection name and keys

        Arguments:
            collection_name {str} -- The name of the collection to delete.
            keys {List[str]} -- The keys of the records to delete.

        Returns:
            None
        """
        async with self._conn.execute(
            f"""
                DELETE FROM {TABLE_NAME} WHERE collection=? and key in (%s)
            """
            % ", ".join("?" * len(keys)),
            (collection_name, *keys),
        ):
            await self._conn.commit()

    async def remove_async(self, collection_name: str, key: str) -> None:
        """Remove a record identified by collection name and key

        Arguments:
            collection_name {str} -- The name of the collection to delete.
            keys {str} -- The key of the record to delete.

        Returns:
            None
        """
        await self.remove_batch_async(collection_name, [key])

    async def get_nearest_matches_async(
        self,
        collection_name: str,
        embedding: np.ndarray,
        limit: int,
        min_relevance_score: float,
        with_embeddings: bool,
    ) -> List[Tuple[MemoryRecord, float]]:
        """Gets the nearest matches to an embedding vector using cosine similarity.
        Because SQLite doesn't have built-in support for vector search, this is done by fetching all the embeddings
        of the given collection. There is an extension sqlite-vss that supports vector search, but it's not stable yet.

        Arguments:
            collection_name {str} -- The name of the collection to get the nearest matches from.
            embedding {ndarray} -- The embedding to find the nearest matches to.
            limit {int} -- The maximum number of matches to return.
            min_relevance_score {float} -- The minimum relevance score of the matches.
            with_embeddings {bool} -- Whether to include the embeddings in the results.

        Returns:
            List[Tuple[MemoryRecord, float]] -- The records and their relevance scores in descending order.
        """
        async with self._conn.execute_fetchall(
            f"""
                SELECT key, metadata, embedding, timestamp FROM {TABLE_NAME} WHERE collection=?
            """,
            [collection_name],
        ) as rows:
            min_heap = []
            for row in rows:
                if row[2] is None:
                    continue
                vector = deserialize_embedding(row[2])
                revelance = np.dot(vector, embedding)
                if revelance < min_relevance_score:
                    continue
                if len(min_heap) == limit:
                    heapq.heappushpop(
                        min_heap, (revelance, row, vector if with_embeddings else None)
                    )
                else:
                    heapq.heappush(
                        min_heap, (revelance, row, vector if with_embeddings else None)
                    )

            result = []
            for relevance, row, vector in min_heap:
                metadata = Metadata.from_json(row[1])
                timestamp = deserialize_timestamp(row[3])
                result.append(
                    (
                        MemoryRecord.local_record(
                            id=row[0] or metadata.id,
                            text=metadata.text,
                            description=metadata.description,
                            additional_metadata=metadata.additional_metadata,
                            embedding=vector if with_embeddings else np.array([]),
                            timestamp=timestamp,
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
        """Gets the nearest match to an embedding vector using cosine similarity.
        Because SQLite doesn't have built-in support for vector search, this is done by fetching all the embeddings
        of the given collection. There is an extension sqlite-vss that supports vector search, but it's not stable yet.

        Arguments:
            collection_name {str} -- The name of the collection to get the nearest matches from.
            embedding {ndarray} -- The embedding to find the nearest matches to.
            limit {int} -- The maximum number of matches to return.
            min_relevance_score {float} -- The minimum relevance score of the matches.
            with_embeddings {bool} -- Whether to include the embeddings in the results.

        Returns:
            Tuple[MemoryRecord, float] -- The record and its relevance score.
        """

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
