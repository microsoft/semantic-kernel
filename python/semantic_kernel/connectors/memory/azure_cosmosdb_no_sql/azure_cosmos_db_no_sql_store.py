# Copyright (c) Microsoft. All rights reserved.

import sys
from collections.abc import Sequence
from typing import Any, TypeVar

from semantic_kernel.connectors.memory.azure_cosmosdb_no_sql.azure_cosmos_db_no_sql_base import AzureCosmosDBNoSQLBase
from semantic_kernel.connectors.memory.azure_cosmosdb_no_sql.azure_cosmos_db_no_sql_collection import (
    AzureCosmosDBNoSQLCollection,
)

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

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
    MemoryConnectorResourceNotFound,
)
from semantic_kernel.utils.experimental_decorator import experimental_class

TModel = TypeVar("TModel")


@experimental_class
class AzureCosmosDBNoSQLStore(AzureCosmosDBNoSQLBase, VectorStore):
    """A VectorStore implementation that uses Azure CosmosDB NoSQL as the backend storage."""

    def __init__(
        self,
        database_name: str,
        url: str | None = None,
        key: str | None = None,
    ):
        """Initialize the AzureCosmosDBNoSQLStore.

        Args:
            database_name (str): The name of the database. The database may not exist yet.
                                 If it does not exist, it will be created when the first collection is created.
            url (str): The URL of the Azure Cosmos DB NoSQL account. Defaults to None.
            key (str): The key of the Azure Cosmos DB NoSQL account. Defaults to None.
        """
        try:
            cosmos_db_nosql_settings = AzureCosmosDBNoSQLSettings.create(url=url, key=key)
        except ValidationError as e:
            raise MemoryConnectorInitializationError("Failed to validate Azure Cosmos DB NoSQL settings.") from e

        super().__init__(
            cosmos_db_nosql_settings=cosmos_db_nosql_settings,
            database_name=database_name,
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
            self.vector_record_collections[collection_name] = AzureCosmosDBNoSQLCollection(
                data_model_type,
                data_model_definition,
                collection_name,
                self.database_name,
            )

        return self.vector_record_collections[collection_name]

    @override
    async def list_collection_names(self, **kwargs) -> Sequence[str]:
        async with self._get_cosmos_client() as cosmos_client:
            if not await self._does_database_exist(cosmos_client):
                raise MemoryConnectorResourceNotFound(f"Database '{self.database_name}' does not exist.")

            try:
                database = self._get_database_proxy(self.database_name, cosmos_client)
                containers = database.list_containers()
                return [container["id"] async for container in containers]
            except Exception as e:
                raise MemoryConnectorException("Failed to list collection names.") from e
