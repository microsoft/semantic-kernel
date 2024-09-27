# Copyright (c) Microsoft. All rights reserved.

from typing import List, Tuple

from numpy import ndarray

from semantic_kernel.connectors.memory.azure_cosmosdb.azure_cosmos_db_store_api import AzureCosmosDBStoreApi
from semantic_kernel.connectors.memory.azure_cosmosdb.cosmosdb_utils import get_mongodb_search_client
from semantic_kernel.connectors.memory.azure_cosmosdb.mongo_vcore_store_api import MongoStoreApi
from semantic_kernel.exceptions import ServiceInitializationError
from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase


class AzureCosmosDBMemoryStore(MemoryStoreBase):
    """A memory store that uses AzureCosmosDB for MongoDB vCore, to perform vector similarity search on a fully
    managed MongoDB compatible database service.
    https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/vcore/vector-search"""

    # Right now this only supports Mongo, but set up to support more later.
    apiStore: AzureCosmosDBStoreApi = None
    mongodb_client = None
    database = None
    index_name = None
    vector_dimensions = None
    num_lists = None
    similarity = None
    collection_name = None

    def __init__(
        self,
        cosmosStore: AzureCosmosDBStoreApi,
        database_name: str,
        index_name: str,
        vector_dimensions: int,
        num_lists: int,
        similarity: str,
    ):
        if vector_dimensions <= 0:
            raise ServiceInitializationError("Vector dimensions must be a positive number.")
        # if connection_string is None:
        #     raise ValueError("Connection String cannot be empty.")
        if database_name is None:
            raise ServiceInitializationError("Database Name cannot be empty.")
        if index_name is None:
            raise ServiceInitializationError("Index Name cannot be empty.")

        self.cosmosStore = cosmosStore
        self.index_name = index_name
        self.num_lists = num_lists
        self.similarity = similarity

    @staticmethod
    async def create(
        cosmos_connstr,
        cosmos_api,
        database_name,
        collection_name,
        index_name,
        vector_dimensions,
        num_lists,
        similarity,
    ) -> MemoryStoreBase:
        """Creates the underlying data store based on the API definition"""
        # Right now this only supports Mongo, but set up to support more later.
        apiStore: AzureCosmosDBStoreApi = None
        if cosmos_api == "mongo-vcore":
            mongodb_client = get_mongodb_search_client(cosmos_connstr)
            database = mongodb_client[database_name]
            apiStore = MongoStoreApi(
                collection_name,
                index_name,
                vector_dimensions,
                num_lists,
                similarity,
                database,
            )
        else:
            raise NotImplementedError(f"API type {cosmos_api} is not supported.")

        store = AzureCosmosDBMemoryStore(
            apiStore,
            database_name,
            index_name,
            vector_dimensions,
            num_lists,
            similarity,
        )
        await store.create_collection(collection_name)
        return store

    async def create_collection(self, collection_name: str) -> None:
        """Creates a new collection in the data store.

        Arguments:
            collection_name {str} -- The name associated with a collection of embeddings.

        Returns:
            None
        """
        return await self.cosmosStore.create_collection(collection_name)

    async def get_collections(self) -> List[str]:
        """Gets the list of collections.

        Returns:
            List[str] -- The list of collections.
        """
        return await self.cosmosStore.get_collections()

    async def delete_collection(self, collection_name: str) -> None:
        """Deletes a collection.

        Arguments:
            collection_name {str} -- The name of the collection to delete.

        Returns:
            None
        """
        return await self.cosmosStore.delete_collection(str())

    async def does_collection_exist(self, collection_name: str) -> bool:
        """Checks if a collection exists.

        Arguments:
            collection_name {str} -- The name of the collection to check.

        Returns:
            bool -- True if the collection exists; otherwise, False.
        """
        return await self.cosmosStore.does_collection_exist(str())

    async def upsert(self, collection_name: str, record: MemoryRecord) -> str:
        """Upsert a record.

        Arguments:
            collection_name {str} -- The name of the collection to upsert the record into.
            record {MemoryRecord} -- The record to upsert.

        Returns:
            str -- The unique record id of the record.
        """
        return await self.cosmosStore.upsert(str(), record)

    async def upsert_batch(self, collection_name: str, records: List[MemoryRecord]) -> List[str]:
        """Upsert a batch of records.

        Arguments:
            collection_name {str}        -- The name of the collection to upsert the records into.
            records {List[MemoryRecord]} -- The records to upsert.

        Returns:
            List[str] -- The unique database keys of the records.
        """
        return await self.cosmosStore.upsert_batch(str(), records)

    async def get(self, collection_name: str, key: str, with_embedding: bool) -> MemoryRecord:
        """Gets a record.

        Arguments:
            collection_name {str} -- The name of the collection to get the record from.
            key {str}             -- The unique database key of the record.
            with_embedding {bool} -- Whether to include the embedding in the result. (default: {False})

        Returns:
            MemoryRecord -- The record.
        """
        return await self.cosmosStore.get(str(), key, with_embedding)

    async def get_batch(self, collection_name: str, keys: List[str], with_embeddings: bool) -> List[MemoryRecord]:
        """Gets a batch of records.

        Arguments:
            collection_name {str}  -- The name of the collection to get the records from.
            keys {List[str]}       -- The unique database keys of the records.
            with_embeddings {bool} -- Whether to include the embeddings in the results. (default: {False})

        Returns:
            List[MemoryRecord] -- The records.
        """
        return await self.cosmosStore.get_batch(str(), keys, with_embeddings)

    async def remove(self, collection_name: str, key: str) -> None:
        """Removes a record.

        Arguments:
            collection_name {str} -- The name of the collection to remove the record from.
            key {str}             -- The unique database key of the record to remove.

        Returns:
            None
        """
        return await self.cosmosStore.remove(str(), key)

    async def remove_batch(self, collection_name: str, keys: List[str]) -> None:
        """Removes a batch of records.

        Arguments:
            collection_name {str} -- The name of the collection to remove the records from.
            keys {List[str]}      -- The unique database keys of the records to remove.

        Returns:
            None
        """
        return await self.cosmosStore.remove_batch(str(), keys)

    async def get_nearest_matches(
        self,
        collection_name: str,
        embedding: ndarray,
        limit: int,
        min_relevance_score: float,
        with_embeddings: bool,
    ) -> List[Tuple[MemoryRecord, float]]:
        """Gets the nearest matches to an embedding using vector configuration.

        Parameters:
            collection_name (str)       -- The name of the collection to get the nearest matches from.
            embedding (ndarray)         -- The embedding to find the nearest matches to.
            limit {int}                 -- The maximum number of matches to return.
            min_relevance_score {float} -- The minimum relevance score of the matches. (default: {0.0})
            with_embeddings {bool}      -- Whether to include the embeddings in the results. (default: {False})

        Returns:
            List[Tuple[MemoryRecord, float]] -- The records and their relevance scores.
        """
        return await self.cosmosStore.get_nearest_matches(str(), embedding, limit, min_relevance_score, with_embeddings)

    async def get_nearest_match(
        self,
        collection_name: str,
        embedding: ndarray,
        min_relevance_score: float,
        with_embedding: bool,
    ) -> Tuple[MemoryRecord, float]:
        """Gets the nearest match to an embedding using vector configuration parameters.

        Arguments:
            collection_name {str}       -- The name of the collection to get the nearest match from.
            embedding {ndarray}         -- The embedding to find the nearest match to.
            min_relevance_score {float} -- The minimum relevance score of the match. (default: {0.0})
            with_embedding {bool}       -- Whether to include the embedding in the result. (default: {False})

        Returns:
            Tuple[MemoryRecord, float] -- The record and the relevance score.
        """
        return await self.cosmosStore.get_nearest_match(str(), embedding, min_relevance_score, with_embedding)
