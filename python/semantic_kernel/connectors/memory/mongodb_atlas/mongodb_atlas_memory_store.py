# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import Mapping
from importlib import metadata
from typing import Any

from motor import core, motor_asyncio
from numpy import ndarray
from pydantic import ValidationError
from pymongo import DeleteOne, ReadPreference, UpdateOne, results
from pymongo.driver_info import DriverInfo

from semantic_kernel.connectors.memory.mongodb_atlas.utils import (
    MONGODB_FIELD_EMBEDDING,
    MONGODB_FIELD_ID,
    NUM_CANDIDATES_SCALAR,
    document_to_memory_record,
    memory_record_to_mongo_document,
)
from semantic_kernel.exceptions import ServiceResourceNotFoundError
from semantic_kernel.exceptions.memory_connector_exceptions import MemoryConnectorInitializationError
from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.utils.feature_stage_decorator import experimental

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class MongoDBAtlasMemoryStore(MemoryStoreBase):
    """Memory Store for MongoDB Atlas Vector Search Connections."""

    def __init__(
        self,
        index_name: str | None = None,
        connection_string: str | None = None,
        database_name: str | None = None,
        read_preference: ReadPreference | None = ReadPreference.PRIMARY,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ):
        """Create the MongoDB Atlas Memory Store.

        Args:
            index_name (str): The name of the index.
            connection_string (str): The connection string for the MongoDB Atlas instance.
            database_name (str): The name of the database.
            read_preference (ReadPreference): The read preference for the connection.
            env_file_path (str): The path to the .env file containing the connection string.
            env_file_encoding (str): The encoding of the .env file.

        """
        from semantic_kernel.connectors.memory.mongodb_atlas.mongodb_atlas_settings import MongoDBAtlasSettings

        try:
            mongodb_settings = MongoDBAtlasSettings(
                database_name=database_name,
                index_name=index_name,
                connection_string=connection_string,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as ex:
            raise MemoryConnectorInitializationError("Failed to create MongoDB Atlas settings.") from ex

        self.mongo_client: motor_asyncio.AsyncIOMotorClient = motor_asyncio.AsyncIOMotorClient(
            mongodb_settings.connection_string.get_secret_value(),
            read_preference=read_preference,
            driver=DriverInfo("Microsoft Semantic Kernel", metadata.version("semantic-kernel")),
        )
        self.database_name: str = mongodb_settings.database_name
        self.index_name: str = mongodb_settings.index_name

    @property
    def database(self) -> core.AgnosticDatabase:
        """The database object."""
        return self.mongo_client[self.database_name]

    @property
    def num_candidates(self) -> int:
        """The number of candidates to return."""
        return self.__num_candidates

    async def close(self):
        """Async close connection, invoked by MemoryStoreBase.__aexit__()."""
        if self.mongo_client:
            self.mongo_client.close()
            del self.mongo_client

    async def create_collection(self, collection_name: str) -> None:
        """Creates a new collection in the data store.

        Args:
            collection_name (str): The name associated with a collection of embeddings.

        Returns:
            None
        """
        if not await self.does_collection_exist(collection_name):
            await self.database.create_collection(collection_name)

    async def get_collections(
        self,
    ) -> list[str]:
        """Gets all collection names in the data store.

        Returns:
            List[str]: A group of collection names.
        """
        return await self.database.list_collection_names()

    async def delete_collection(self, collection_name: str) -> None:
        """Deletes a collection from the data store.

        Args:
            collection_name (str): The name associated with a collection of embeddings.

        Returns:
            None
        """
        await self.database[collection_name].drop()

    async def does_collection_exist(self, collection_name: str) -> bool:
        """Determines if a collection exists in the data store.

        Args:
            collection_name (str): The name associated with a collection of embeddings.

        Returns:
            bool: True if given collection exists, False if not.
        """
        return collection_name in (await self.get_collections())

    async def upsert(self, collection_name: str, record: MemoryRecord) -> str:
        """Upserts a memory record into the data store.

        Does not guarantee that the collection exists.
            If the record already exists, it will be updated.
            If the record does not exist, it will be created.

        Args:
            collection_name (str): The name associated with a collection of embeddings.
            record (MemoryRecord): The memory record to upsert.

        Returns:
            str: The unique identifier for the memory record.
        """
        document: Mapping[str, Any] = memory_record_to_mongo_document(record)

        update_result: results.UpdateResult = await self.database[collection_name].update_one(
            document, {"$set": document}, upsert=True
        )

        if not update_result.acknowledged:
            raise ValueError("Upsert failed")
        return record._id

    async def upsert_batch(self, collection_name: str, records: list[MemoryRecord]) -> list[str]:
        """Upserts a group of memory records into the data store.

        Does not guarantee that the collection exists.
            If the record already exists, it will be updated.
            If the record does not exist, it will be created.

        Args:
            collection_name (str): The name associated with a collection of embeddings.
            records (MemoryRecord): The memory records to upsert.

        Returns:
            List[str]: The unique identifiers for the memory records.
        """
        upserts: list[UpdateOne] = []
        for record in records:
            document = memory_record_to_mongo_document(record)
            upserts.append(UpdateOne(document, {"$set": document}, upsert=True))
        bulk_update_result: results.BulkWriteResult = await self.database[collection_name].bulk_write(
            upserts, ordered=False
        )

        # Assert the number matched and the number upserted equal the total batch updated
        logger.debug(
            "matched_count=%s, upserted_count=%s",
            bulk_update_result.matched_count,
            bulk_update_result.upserted_count,
        )
        if bulk_update_result.matched_count + bulk_update_result.upserted_count != len(records):
            raise ValueError("Batch upsert failed")
        return [record._id for record in records]

    async def get(self, collection_name: str, key: str, with_embedding: bool) -> MemoryRecord:
        """Gets a memory record from the data store. Does not guarantee that the collection exists.

        Args:
            collection_name (str): The name associated with a collection of embeddings.
            key (str): The unique id associated with the memory record to get.
            with_embedding (bool): If true, the embedding will be returned in the memory record.

        Returns:
            MemoryRecord: The memory record if found
        """
        document = await self.database[collection_name].find_one({MONGODB_FIELD_ID: key})

        return document_to_memory_record(document, with_embedding) if document else None

    async def get_batch(self, collection_name: str, keys: list[str], with_embeddings: bool) -> list[MemoryRecord]:
        """Gets a batch of memory records from the data store. Does not guarantee that the collection exists.

        Args:
            collection_name (str): The name associated with a collection of embeddings.
            keys (List[str]): The unique ids associated with the memory records to get.
            with_embeddings (bool): If true, the embedding will be returned in the memory records.

        Returns:
            List[MemoryRecord]: The memory records associated with the unique keys provided.
        """
        results = self.database[collection_name].find({MONGODB_FIELD_ID: {"$in": keys}})

        return [
            document_to_memory_record(result, with_embeddings) for result in await results.to_list(length=len(keys))
        ]

    async def remove(self, collection_name: str, key: str) -> None:
        """Removes a memory record from the data store. Does not guarantee that the collection exists.

        Args:
            collection_name (str): The name associated with a collection of embeddings.
            key (str): The unique id associated with the memory record to remove.

        Returns:
            None
        """
        if not await self.does_collection_exist(collection_name):
            raise ServiceResourceNotFoundError(f"collection {collection_name} not found")
        await self.database[collection_name].delete_one({MONGODB_FIELD_ID: key})

    async def remove_batch(self, collection_name: str, keys: list[str]) -> None:
        """Removes a batch of memory records from the data store. Does not guarantee that the collection exists.

        Args:
            collection_name (str): The name associated with a collection of embeddings.
            keys (List[str]): The unique ids associated with the memory records to remove.

        Returns:
            None
        """
        if not await self.does_collection_exist(collection_name):
            raise ServiceResourceNotFoundError(f"collection {collection_name} not found")
        deletes: list[DeleteOne] = [DeleteOne({MONGODB_FIELD_ID: key}) for key in keys]
        bulk_write_result = await self.database[collection_name].bulk_write(deletes, ordered=False)
        logger.debug("%s entries deleted", bulk_write_result.deleted_count)

    async def get_nearest_matches(
        self,
        collection_name: str,
        embedding: ndarray,
        limit: int,
        with_embeddings: bool,
        min_relevance_score: float | None = None,
    ) -> list[tuple[MemoryRecord, float]]:
        """Gets the nearest matches to an embedding of type float. Does not guarantee that the collection exists.

        Args:
            collection_name (str): The name associated with a collection of embeddings.
            embedding (ndarray): The embedding to compare the collection's embeddings with.
            limit (int): The maximum number of similarity results to return, defaults to 1.
            min_relevance_score (float): The minimum relevance threshold for returned results.
            with_embeddings (bool): If true, the embeddings will be returned in the memory records.

        Returns:
            List[Tuple[MemoryRecord, float]]: A list of tuples where item1 is a MemoryRecord and item2
                is its similarity score as a float.
        """
        pipeline: list[dict[str, Any]] = []
        vector_search_query: list[Mapping[str, Any]] = {
            "$vectorSearch": {
                "queryVector": embedding.tolist(),
                "limit": limit,
                "numCandidates": limit * NUM_CANDIDATES_SCALAR,
                "path": MONGODB_FIELD_EMBEDDING,
                "index": self.index_name,
            }
        }

        pipeline.append(vector_search_query)
        # add meta search scoring
        pipeline.append({"$set": {"score": {"$meta": "vectorSearchScore"}}})

        if min_relevance_score is not None:
            pipeline.append({"$match": {"score": {"$gte": min_relevance_score}}})

        cursor = self.database[collection_name].aggregate(pipeline)

        return [
            (
                document_to_memory_record(doc, with_embeddings=with_embeddings),
                doc["score"],
            )
            for doc in await cursor.to_list(length=limit)
        ]

    async def get_nearest_match(
        self,
        collection_name: str,
        embedding: ndarray,
        with_embedding: bool,
        min_relevance_score: float | None = None,
    ) -> tuple[MemoryRecord, float]:
        """Gets the nearest match to an embedding of type float. Does not guarantee that the collection exists.

        Args:
            collection_name (str): The name associated with a collection of embeddings.
            embedding (ndarray): The embedding to compare the collection's embeddings with.
            min_relevance_score (float): The minimum relevance threshold for returned result.
            with_embedding (bool): If true, the embeddings will be returned in the memory record.

        Returns:
            Tuple[MemoryRecord, float]: A tuple consisting of the MemoryRecord and the similarity score as a float.
        """
        matches: list[tuple[MemoryRecord, float]] = await self.get_nearest_matches(
            collection_name=collection_name,
            embedding=embedding,
            limit=1,
            min_relevance_score=min_relevance_score,
            with_embeddings=with_embedding,
        )

        return matches[0] if matches else None
