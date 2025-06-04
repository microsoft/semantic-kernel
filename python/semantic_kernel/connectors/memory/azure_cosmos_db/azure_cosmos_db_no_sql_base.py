# Copyright (c) Microsoft. All rights reserved.

from azure.cosmos.aio import ContainerProxy, CosmosClient, DatabaseProxy
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from pydantic import ValidationError

from semantic_kernel.connectors.memory.azure_cosmos_db.azure_cosmos_db_no_sql_settings import AzureCosmosDBNoSQLSettings
from semantic_kernel.connectors.memory.azure_cosmos_db.utils import CosmosClientWrapper
from semantic_kernel.exceptions import (
    VectorStoreInitializationException,
    VectorStoreOperationException,
)
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.authentication.async_default_azure_credential_wrapper import (
    AsyncDefaultAzureCredentialWrapper,
)
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class AzureCosmosDBNoSQLBase(KernelBaseModel):
    """An Azure Cosmos DB NoSQL collection stores documents in a Azure Cosmos DB NoSQL account."""

    cosmos_client: CosmosClient
    database_name: str
    cosmos_db_nosql_settings: AzureCosmosDBNoSQLSettings
    # If create_database is True, the database will be created
    # if it does not exist when an operation requires a database.
    create_database: bool

    def __init__(
        self,
        url: str | None = None,
        key: str | None = None,
        database_name: str | None = None,
        cosmos_client: CosmosClient | None = None,
        create_database: bool = False,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
        **kwargs,
    ):
        """Initialize the AzureCosmosDBNoSQLBase.

        Args:
            url (str): The URL of the Azure Cosmos DB NoSQL account. Defaults to None.
            key (str): The key of the Azure Cosmos DB NoSQL account. Defaults to None.
            database_name (str): The name of the database. The database may not exist yet. If it does not exist,
                                 it will be created when the first collection is created. Defaults to None.
            cosmos_client (CosmosClient): The custom Azure Cosmos DB NoSQL client whose lifetime is managed by the user.
                                          Defaults to None.
            create_database (bool): If True, the database will be created if it does not exist.
                                    Defaults to False.
            env_file_path (str): The path to the .env file. Defaults to None.
            env_file_encoding (str): The encoding of the .env file. Defaults to None.
            kwargs: Additional keyword arguments.
        """
        try:
            cosmos_db_nosql_settings = AzureCosmosDBNoSQLSettings(
                url=url,
                key=key,
                database_name=database_name,
                env_file_path=env_file_path,
                env_file_encoding=env_file_encoding,
            )
        except ValidationError as e:
            raise VectorStoreInitializationException("Failed to validate Azure Cosmos DB NoSQL settings.") from e

        if cosmos_db_nosql_settings.database_name is None:
            raise VectorStoreInitializationException("The name of the Azure Cosmos DB NoSQL database is missing.")

        if cosmos_client is None:
            if cosmos_db_nosql_settings.key is not None:
                cosmos_client = CosmosClientWrapper(
                    str(cosmos_db_nosql_settings.url), credential=cosmos_db_nosql_settings.key.get_secret_value()
                )
            else:
                cosmos_client = CosmosClientWrapper(
                    str(cosmos_db_nosql_settings.url), credential=AsyncDefaultAzureCredentialWrapper()
                )

        super().__init__(
            cosmos_client=cosmos_client,
            database_name=cosmos_db_nosql_settings.database_name,
            cosmos_db_nosql_settings=cosmos_db_nosql_settings,
            create_database=create_database,
            **kwargs,
        )

    async def _does_database_exist(self) -> bool:
        """Checks if the database exists."""
        try:
            await self.cosmos_client.get_database_client(self.database_name).read()
            return True
        except CosmosResourceNotFoundError:
            return False
        except Exception as e:
            raise VectorStoreOperationException(
                f"Failed to check if database '{self.database_name}' exists, with message {e}"
            ) from e

    async def _get_database_proxy(self, **kwargs) -> DatabaseProxy:
        """Gets the database proxy."""
        try:
            if await self._does_database_exist():
                return self.cosmos_client.get_database_client(self.database_name)

            if self.create_database:
                return await self.cosmos_client.create_database(self.database_name, **kwargs)
            raise VectorStoreOperationException(f"Database '{self.database_name}' does not exist.")
        except Exception as e:
            raise VectorStoreOperationException(f"Failed to get database proxy for '{id}'.") from e

    async def _get_container_proxy(self, container_name: str, **kwargs) -> ContainerProxy:
        """Gets the container proxy."""
        try:
            database_proxy = await self._get_database_proxy(**kwargs)
            return database_proxy.get_container_client(container_name)
        except Exception as e:
            raise VectorStoreOperationException(f"Failed to get container proxy for '{container_name}'.") from e
