# Copyright (c) Microsoft. All rights reserved.

import uuid
from logging import Logger
from typing import List, Optional

from numpy import ndarray

from semantic_kernel.memory.azure_cosmosdb_mongo_memory_store.utils import (
    DEFAULT_INSERT_BATCH_SIZE,
    SEARCH_FIELD_EMBEDDING,
    SEARCH_FIELD_ID,
    dict_to_memory_record,
    get_mongodb_resources,
    memory_record_to_mongodb_record,
)
from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.utils.null_logger import NullLogger


class AzureCosmosDBMongoDBMemoryStore(MemoryStoreBase):
    """
    A class representing a memory store for Azure Cosmos DB MongoDB API.

    Args:
        vector_size (int): The size of the vector.
        connection_string (str, optional): The connection string for the MongoDB client.
        database_name (str, optional): The name of the MongoDB database.
        embedding_key (str, optional): The key used for embedding. Defaults to SEARCH_FIELD_EMBEDDING.
        batch_size (int, optional): The batch size for inserting records. Defaults to DEFAULT_INSERT_BATCH_SIZE.
        logger (Optional[Logger], optional): The logger instance. Defaults to None.
    """

    _mongodb_client = None
    _vector_size: int = None
    _logger: Logger = None
    _database = None
    _embedding_key = None
    _batch_size = None

    def __init__(
        self,
        vector_size: int,
        connection_string: str = None,
        database_name: str = None,
        embedding_key: str = SEARCH_FIELD_EMBEDDING,
        batch_size: int = DEFAULT_INSERT_BATCH_SIZE,
        logger: Optional[Logger] = None,
    ) -> None:
        if vector_size <= 0:
            raise ValueError("Vector dimension must be a positive integer")

        if embedding_key is None:
            raise ValueError("embedding_key must be specified")

        if database_name is None:
            raise ValueError("database_name must be specified")

        self._mongodb_client, self._database = get_mongodb_resources(
            connection_string, database_name
        )
        self._embedding_key = embedding_key
        self._vector_size = vector_size
        self.batch_size = batch_size
        self._logger = logger or NullLogger()

    async def close_async(self):
        """Async close connection, invoked by MemoryStoreBase.__aexit__()"""
        if self._mongodb_client is not None:
            await self._mongodb_client.close()

    async def create_collection_async(
        self,
        collection_name: str,
        similarity: str = "COS",
        num_lists: int = 100,
    ) -> None:
        """
        Creates a new collection in the MongoDB database with the given name,
        if it does not already exist.
        Also creates an index on the collection for vector search
        using the given similarity metric and number of lists.

        Args:
            collection_name (str): The name of the collection to create.
            similarity (str, optional): The similarity metric to use with the IVF index.
                                        Possible options are COS (cosine distance),
                                        L2 (Euclidean distance),
                                        and IP (inner product). Defaults to "COS".
            num_lists (int, optional): The number of clusters that the inverted file
                                        (IVF) index
                                        uses to group the vector data. Defaults to 100.

        Returns:
            None
        """
        if collection_name not in self._database.list_collection_names():
            self._database.command(
                {
                    "createIndexes": collection_name,
                    "indexes": [
                        {
                            "name": "vectorSearchIndex",
                            "key": {self._embedding_key: "cosmosSearch"},
                            "cosmosSearchOptions": {
                                "kind": "vector-ivf",
                                "numLists": num_lists,
                                "similarity": similarity,
                                "dimensions": self._vector_size,
                            },
                        }
                    ],
                }
            )

    async def get_collections_async(self) -> List[str]:
        """Gets the list of collections.

        Returns:
            List[str] -- The list of collections.
        """

        return self._database.list_collection_names()

    async def delete_collection_async(self, collection_name: str) -> None:
        """Deletes a collection.

        Arguments:
            collection_name {str} -- The name of the collection to delete.

        Returns:
            None
        """
        collection = self._database[collection_name]
        collection.drop()

    async def does_collection_exist_async(self, collection_name: str) -> bool:
        """Checks if a collection exists.

        Arguments:
            collection_name {str} -- The name of the collection to check.

        Returns:
            bool -- True if the collection exists; otherwise, False.
        """
        if collection_name in self._database.list_collection_names():
            return True
        else:
            return False

    async def upsert_async(self, collection_name: str, record: MemoryRecord) -> str:
        """Upsert a record.

        Arguments:
            collection_name {str} -- The name of the collection to upsert the record into.
            record {MemoryRecord} -- The record to upsert.

        Returns:
            str -- The unique record id of the record.
        """

        result = await self.upsert_batch_async(collection_name, [record])
        if result:
            return result[0]
        return None

    async def upsert_batch_async(
        self, collection_name: str, records: List[MemoryRecord]
    ) -> List[str]:
        """Upsert a batch of records.

        Arguments:
            collection_name {str}        -- The name of the collection to upsert the
                                            records into.
            records {List[MemoryRecord]} -- The records to upsert.

        Returns:
            List[str] -- The unique database keys of the records.
        """

        mongodb_records = []
        inserted_ids = []
        collection = self._database[collection_name]
        for record in records:
            if not record._id:
                record._id = str(uuid.uuid4())

            existing_document = collection.find_one({SEARCH_FIELD_ID: record._id})

            if existing_document:
                # Update the existing document
                update_result = collection.update_one(
                    {SEARCH_FIELD_ID: record._id},
                    {"$set": memory_record_to_mongodb_record(record)},
                )
                if update_result.modified_count > 0:
                    print(f"Updated existing document with _id: {record._id}")
            else:
                mongodb_record = memory_record_to_mongodb_record(record)
                mongodb_records.append(mongodb_record)

                if len(mongodb_records) == DEFAULT_INSERT_BATCH_SIZE:
                    result = collection.insert_many(mongodb_records)
                    inserted_ids.extend(result.inserted_ids)
                    mongodb_records.clear()

        if mongodb_records:
            result = collection.insert_many(mongodb_records)
            inserted_ids.extend(result.inserted_ids)

        return inserted_ids

    async def get_async(self, collection_name: str, key: str) -> MemoryRecord:
        """Gets a record.

        Arguments:
            collection_name {str} -- The name of the collection to get the record from.
            key {str}             -- The unique database key of the record.

        Returns:
            MemoryRecord -- The record.
        """

        query = {SEARCH_FIELD_ID: key}
        collection = self._database[collection_name]

        for doc in collection.find(query):
            return dict_to_memory_record(doc)

    async def get_batch_async(
        self, collection_name: str, keys: List[str]
    ) -> List[MemoryRecord]:
        search_results = []
        collection = self._database[collection_name]

        for key in keys:
            query = {SEARCH_FIELD_ID: key}
            result_cursor = collection.find(query)

            for document in result_cursor:
                memory_record = dict_to_memory_record(document)
                search_results.append(memory_record)

        return search_results

    async def remove_batch_async(self, collection_name: str, keys: List[str]) -> None:
        """Removes a batch of records.

        Arguments:
            collection_name {str} -- The name of the collection to remove the records from.
            keys {List[str]}      -- The unique database keys of the records to remove.

        Returns:
            None
        """
        collection = self._database[collection_name]
        for key in keys:
            docs_to_delete = {SEARCH_FIELD_ID: key}
            collection.delete_one(docs_to_delete)

    async def remove_async(self, collection_name: str, key: str) -> None:
        collection = self._database[collection_name]
        docs_to_delete = {SEARCH_FIELD_ID: key}
        collection.delete_one(docs_to_delete)

    async def get_nearest_match_async(
        self, collection_name: str, embedding: ndarray
    ) -> MemoryRecord:
        memory_records = await self.get_nearest_matches_async(
            collection_name=collection_name,
            embedding=embedding,
            limit=1,
        )
        if len(memory_records) > 0:
            return memory_records[0]
        return None

    async def get_nearest_matches_async(
        self,
        collection_name: str,
        embedding: ndarray,
        limit: int = 1,
    ) -> List[MemoryRecord]:
        """
        Returns a list of nearest matching records from the specified collection based on
        the provided embedding.

        Args:
            collection_name (str): The name of the collection to search.
            embedding (ndarray): The embedding to search for.
            limit (int, optional): The maximum number of matching records to return.
            Defaults to 1.

        Returns:
            List[MemoryRecord]: A list of matching records and their
            corresponding similarity scores.
        """

        search_pipeline = [
            {
                "$search": {
                    "cosmosSearch": {
                        "vector": embedding.tolist(),
                        "path": self._embedding_key,
                        "k": limit,
                    },
                    "returnStoredSource": True,
                }
            },
        ]

        collection = self._database[collection_name]
        search_cursor = collection.aggregate(search_pipeline)

        matching_records = []
        for result in search_cursor:
            matching_records.append(dict_to_memory_record(result))

        return matching_records
