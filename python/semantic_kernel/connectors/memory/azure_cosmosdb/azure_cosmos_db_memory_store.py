# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Literal

from numpy import ndarray
from pymongo import MongoClient

from semantic_kernel.connectors.memory.azure_cosmosdb.azure_cosmos_db_store_api import AzureCosmosDBStoreApi
from semantic_kernel.connectors.memory.azure_cosmosdb.azure_cosmosdb_settings import AzureCosmosDBSettings
from semantic_kernel.connectors.memory.azure_cosmosdb.mongo_vcore_store_api import MongoStoreApi
from semantic_kernel.connectors.memory.azure_cosmosdb.utils import (
    CosmosDBSimilarityType,
    CosmosDBVectorSearchType,
)
from semantic_kernel.exceptions import MemoryConnectorInitializationError
from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.memory.memory_store_base import MemoryStoreBase
from semantic_kernel.utils.feature_stage_decorator import experimental

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class AzureCosmosDBMemoryStore(MemoryStoreBase):
    """A memory store that uses AzureCosmosDB for MongoDB vCore.

    To perform vector similarity search on a fully managed MongoDB compatible database service.
    https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/vcore/vector-search.
    """

    # Right now this only supports Mongo, but set up to support more later.
    api_store: AzureCosmosDBStoreApi = None
    mongodb_client = None
    database = None
    index_name = None
    vector_dimensions = None
    num_lists = None
    similarity = None
    collection_name = None
    kind = None
    m = None
    ef_construction = None
    ef_search = None

    def __init__(
        self,
        cosmosStore: AzureCosmosDBStoreApi,
        database_name: str,
        index_name: str,
        vector_dimensions: int,
        num_lists: int = 100,
        similarity: CosmosDBSimilarityType = CosmosDBSimilarityType.COS,
        kind: CosmosDBVectorSearchType = CosmosDBVectorSearchType.VECTOR_HNSW,
        m: int = 16,
        ef_construction: int = 64,
        ef_search: int = 40,
    ):
        """Initializes a new instance of the AzureCosmosDBMemoryStore class."""
        if vector_dimensions <= 0:
            raise MemoryConnectorInitializationError("Vector dimensions must be a positive number.")
        if database_name is None:
            raise MemoryConnectorInitializationError("Database Name cannot be empty.")
        if index_name is None:
            raise MemoryConnectorInitializationError("Index Name cannot be empty.")

        self.cosmos_store = cosmosStore
        self.index_name = index_name
        self.num_lists = num_lists
        self.similarity = similarity
        self.kind = kind
        self.m = m
        self.ef_construction = ef_construction
        self.ef_search = ef_search

    @staticmethod
    async def create(
        database_name: str,
        collection_name: str,
        vector_dimensions: int,
        num_lists: int,
        similarity: CosmosDBSimilarityType,
        kind: CosmosDBVectorSearchType,
        m: int,
        ef_construction: int,
        ef_search: int,
        index_name: str | None = None,
        cosmos_connstr: str | None = None,
        application_name: str | None = None,
        cosmos_api: Literal["mongo-vcore"] = "mongo-vcore",
        env_file_path: str | None = None,
    ) -> MemoryStoreBase:
        """Creates the underlying data store based on the API definition."""
        # Right now this only supports Mongo, but set up to support more later.
        api_store: AzureCosmosDBStoreApi = None
        if cosmos_api == "mongo-vcore":
            cosmosdb_settings = AzureCosmosDBSettings(
                env_file_path=env_file_path,
                connection_string=cosmos_connstr,
            )

            mongodb_client = MongoClient(
                cosmosdb_settings.connection_string.get_secret_value() if cosmosdb_settings.connection_string else None,
                appname=application_name,
            )
            database = mongodb_client[database_name]
            api_store = MongoStoreApi(
                collection_name=collection_name,
                index_name=index_name,
                vector_dimensions=vector_dimensions,
                num_lists=num_lists,
                similarity=similarity,
                database=database,
                kind=kind,
                m=m,
                ef_construction=ef_construction,
                ef_search=ef_search,
            )
        else:
            raise MemoryConnectorInitializationError(f"API type {cosmos_api} is not supported.")

        store = AzureCosmosDBMemoryStore(
            api_store,
            database_name,
            index_name,
            vector_dimensions,
            num_lists,
            similarity,
            kind,
            m,
            ef_construction,
            ef_search,
        )
        await store.create_collection(collection_name)
        return store

    async def create_collection(self, collection_name: str) -> None:
        """Creates a new collection in the data store.

        Args:
            collection_name (str): The name associated with a collection of embeddings.

        Returns:
            None
        """
        return await self.cosmos_store.create_collection(collection_name)

    async def get_collections(self) -> list[str]:
        """Gets the list of collections.

        Returns:
            List[str]: The list of collections.
        """
        return await self.cosmos_store.get_collections()

    async def delete_collection(self, collection_name: str) -> None:
        """Deletes a collection.

        Args:
            collection_name (str): The name of the collection to delete.

        Returns:
            None
        """
        return await self.cosmos_store.delete_collection("")

    async def does_collection_exist(self, collection_name: str) -> bool:
        """Checks if a collection exists.

        Args:
            collection_name (str): The name of the collection to check.

        Returns:
            bool: True if the collection exists; otherwise, False.
        """
        return await self.cosmos_store.does_collection_exist("")

    async def upsert(self, collection_name: str, record: MemoryRecord) -> str:
        """Upsert a record.

        Args:
            collection_name (str): The name of the collection to upsert the record into.
            record (MemoryRecord): The record to upsert.

        Returns:
            str: The unique record id of the record.
        """
        return await self.cosmos_store.upsert("", record)

    async def upsert_batch(self, collection_name: str, records: list[MemoryRecord]) -> list[str]:
        """Upsert a batch of records.

        Args:
            collection_name (str): The name of the collection to upsert the records into.
            records (List[MemoryRecord]): The records to upsert.

        Returns:
            List[str]: The unique database keys of the records.
        """
        return await self.cosmos_store.upsert_batch("", records)

    async def get(self, collection_name: str, key: str, with_embedding: bool) -> MemoryRecord:
        """Gets a record.

        Args:
            collection_name (str): The name of the collection to get the record from.
            key (str): The unique database key of the record.
            with_embedding (bool): Whether to include the embedding in the result. (default: {False})

        Returns:
            MemoryRecord: The record.
        """
        return await self.cosmos_store.get("", key, with_embedding)

    async def get_batch(self, collection_name: str, keys: list[str], with_embeddings: bool) -> list[MemoryRecord]:
        """Gets a batch of records.

        Args:
            collection_name (str): The name of the collection to get the records from.
            keys (List[str]): The unique database keys of the records.
            with_embeddings (bool): Whether to include the embeddings in the results. (default: {False})

        Returns:
            List[MemoryRecord]: The records.
        """
        return await self.cosmos_store.get_batch("", keys, with_embeddings)

    async def remove(self, collection_name: str, key: str) -> None:
        """Removes a record.

        Args:
            collection_name (str): The name of the collection to remove the record from.
            key (str): The unique database key of the record to remove.

        Returns:
            None
        """
        return await self.cosmos_store.remove("", key)

    async def remove_batch(self, collection_name: str, keys: list[str]) -> None:
        """Removes a batch of records.

        Args:
            collection_name (str): The name of the collection to remove the records from.
            keys (List[str]): The unique database keys of the records to remove.

        Returns:
            None
        """
        return await self.cosmos_store.remove_batch("", keys)

    async def get_nearest_matches(
        self,
        collection_name: str,
        embedding: ndarray,
        limit: int,
        min_relevance_score: float,
        with_embeddings: bool,
    ) -> list[tuple[MemoryRecord, float]]:
        """Gets the nearest matches to an embedding using vector configuration.

        Parameters:
            collection_name (str)      : The name of the collection to get the nearest matches from.
            embedding (ndarray)        : The embedding to find the nearest matches to.
            limit (int): The maximum number of matches to return.
            min_relevance_score (float): The minimum relevance score of the matches. (default: {0.0})
            with_embeddings (bool): Whether to include the embeddings in the results. (default: {False})

        Returns:
            List[Tuple[MemoryRecord, float]]: The records and their relevance scores.
        """
        return await self.cosmos_store.get_nearest_matches("", embedding, limit, min_relevance_score, with_embeddings)

    async def get_nearest_match(
        self,
        collection_name: str,
        embedding: ndarray,
        min_relevance_score: float,
        with_embedding: bool,
    ) -> tuple[MemoryRecord, float]:
        """Gets the nearest match to an embedding using vector configuration parameters.

        Args:
            collection_name (str): The name of the collection to get the nearest match from.
            embedding (ndarray): The embedding to find the nearest match to.
            min_relevance_score (float): The minimum relevance score of the match. (default: {0.0})
            with_embedding (bool): Whether to include the embedding in the result. (default: {False})

        Returns:
            Tuple[MemoryRecord, float]: The record and the relevance score.
        """
        return await self.cosmos_store.get_nearest_match("", embedding, min_relevance_score, with_embedding)
