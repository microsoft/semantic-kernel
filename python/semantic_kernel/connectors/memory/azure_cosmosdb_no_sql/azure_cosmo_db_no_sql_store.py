# Copyright (c) Microsoft. All rights reserved.

import sys
from collections.abc import Sequence
from typing import Any, TypeVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from azure.cosmos.aio import CosmosClient
from azure.identity import DefaultAzureCredential
from pydantic import ValidationError

from semantic_kernel.connectors.memory.azure_cosmosdb_no_sql.azure_cosmos_db_no_sql_settings import (
    AzureCosmosDBNoSQLSettings,
)
from semantic_kernel.data.vector_store import VectorStore
from semantic_kernel.data.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_store_record_collection import VectorStoreRecordCollection
from semantic_kernel.exceptions.memory_connector_exceptions import (
    MemoryConnectorException,
    MemoryConnectorInitializationError,
)
from semantic_kernel.utils.experimental_decorator import experimental_class

TModel = TypeVar("TModel")


@experimental_class
class AzureCosmosDBNoSQLStore(VectorStore):
    """A VectorStore implementation that uses Azure CosmosDB NoSQL as the backend storage."""

    cosmos_client: CosmosClient | None
    database_name: str | None

    def __init__(
        self,
        database_name: str,
        url: str | None = None,
        key: str | None = None,
        cosmos_client: CosmosClient = None,
    ):
        """Initialize the AzureCosmosDBNoSQLStore.

        Args:
            database_name (str): The name of the database.
            url (str): The URL of the Azure Cosmos DB NoSQL account. Defaults to None.
            key (str): The key of the Azure Cosmos DB NoSQL account. Defaults to None.
            cosmos_client (CosmosClient): A custom Cosmos client. Used to create a database proxy if
                                          not provided. Defaults to None.
        """
        if not cosmos_client:
            try:
                cosmos_db_nosql_settings = AzureCosmosDBNoSQLSettings.create(url=url, key=key)
            except ValidationError as e:
                raise MemoryConnectorInitializationError("Failed to validate Azure Cosmos DB NoSQL settings.") from e

            if cosmos_db_nosql_settings.key:
                cosmos_client = CosmosClient(url, credential=key)
            else:
                cosmos_client = CosmosClient(url, DefaultAzureCredential())

        super().__init__(
            database_name=database_name,
            cosmos_client=cosmos_client,
        )

    @override
    def get_collection(
        self,
        collection_name: str,
        data_model_type: type[object],
        data_model_definition: VectorStoreRecordDefinition | None = None,
        **kwargs: Any,
    ) -> VectorStoreRecordCollection:
        if collection_name not in self.vector_record_collections:
            self.vector_record_collections[collection_name] = VectorStoreRecordCollection(
                data_model_type,
                data_model_definition,
                collection_name,
                self.database_name,
                self.cosmos_client,
            )

        return self.vector_record_collections[collection_name]

    @override
    async def list_collection_names(self, **kwargs) -> Sequence[str]:
        async with self.cosmos_client:
            try:
                databases = await self.cosmos_client.create_database_if_not_exists(id=self.database_name)
                containers = databases.list_containers()
                return [container["id"] async for container in containers]
            except Exception as e:
                raise MemoryConnectorException("Failed to list collection names.") from e
