# Copyright (c) Microsoft. All rights reserved.

from azure.cosmos.aio import ContainerProxy, CosmosClient, DatabaseProxy
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from azure.identity import DefaultAzureCredential

from semantic_kernel.connectors.memory.azure_cosmosdb_no_sql.azure_cosmos_db_no_sql_settings import (
    AzureCosmosDBNoSQLSettings,
)
from semantic_kernel.exceptions.memory_connector_exceptions import MemoryConnectorResourceNotFound
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class AzureCosmosDBNoSQLBase(KernelBaseModel):
    """An Azure Cosmos DB NoSQL collection stores documents in a Azure Cosmos DB NoSQL account."""

    cosmos_db_nosql_settings: AzureCosmosDBNoSQLSettings
    database_name: str

    def _get_cosmos_client(self) -> CosmosClient:
        """Gets the Cosmos client.

        We cannot cache the Cosmos client because it is only good for one context.
        https://github.com/Azure/azure-sdk-for-python/issues/25640
        """
        if not self.cosmos_db_nosql_settings.key:
            return CosmosClient(str(self.cosmos_db_nosql_settings.url), DefaultAzureCredential())

        return CosmosClient(
            str(self.cosmos_db_nosql_settings.url),
            credential=self.cosmos_db_nosql_settings.key.get_secret_value(),
        )

    async def _does_database_exist(self, cosmos_client: CosmosClient) -> bool:
        """Checks if the database exists."""
        try:
            cosmos_client.get_database_client(self.database_name)
            return True
        except CosmosResourceNotFoundError:
            return False
        except Exception as e:
            raise MemoryConnectorResourceNotFound(f"Failed to check if database '{self.database_name}' exists.") from e

    def _get_database_proxy(self, id: str, cosmos_client: CosmosClient) -> DatabaseProxy:
        """Gets the database proxy.

        The database must exist before calling this method.
        """
        try:
            return cosmos_client.get_database_client(id)
        except Exception as e:
            raise MemoryConnectorResourceNotFound(f"Failed to get database proxy for '{id}'.") from e

    def _get_container_proxy(self, container_name: str, cosmos_client: CosmosClient) -> ContainerProxy:
        """Gets the container proxy.

        The container must exist before calling this method.
        """
        try:
            database_proxy = self._get_database_proxy(self.database_name, cosmos_client)
            return database_proxy.get_container_client(container_name)
        except Exception as e:
            raise MemoryConnectorResourceNotFound(f"Failed to get container proxy for '{container_name}'.") from e
