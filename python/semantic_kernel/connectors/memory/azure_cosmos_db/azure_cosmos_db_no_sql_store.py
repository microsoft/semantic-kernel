# Copyright (c) Microsoft. All rights reserved.

import sys
from collections.abc import Sequence
from typing import Any, TypeVar

from azure.cosmos.aio import CosmosClient

from semantic_kernel.connectors.memory.azure_cosmos_db.azure_cosmos_db_no_sql_base import AzureCosmosDBNoSQLBase
from semantic_kernel.connectors.memory.azure_cosmos_db.azure_cosmos_db_no_sql_collection import (
    AzureCosmosDBNoSQLCollection,
)
from semantic_kernel.data.record_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_storage import VectorStore, VectorStoreRecordCollection
from semantic_kernel.exceptions import VectorStoreOperationException
from semantic_kernel.utils.feature_stage_decorator import experimental

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

TModel = TypeVar("TModel")


@experimental
class AzureCosmosDBNoSQLStore(AzureCosmosDBNoSQLBase, VectorStore):
    """A VectorStore implementation that uses Azure CosmosDB NoSQL as the backend storage."""

    def __init__(
        self,
        url: str | None = None,
        key: str | None = None,
        database_name: str | None = None,
        cosmos_client: CosmosClient | None = None,
        create_database: bool = False,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ):
        """Initialize the AzureCosmosDBNoSQLStore.

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
        """
        super().__init__(
            url=url,
            key=key,
            database_name=database_name,
            cosmos_client=cosmos_client,
            create_database=create_database,
            env_file_path=env_file_path,
            env_file_encoding=env_file_encoding,
            managed_client=cosmos_client is None,
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
                collection_name,
                database_name=self.database_name,
                data_model_definition=data_model_definition,
                cosmos_client=self.cosmos_client,
                create_database=self.create_database,
                env_file_path=self.cosmos_db_nosql_settings.env_file_path,
                env_file_encoding=self.cosmos_db_nosql_settings.env_file_encoding,
                **kwargs,
            )

        return self.vector_record_collections[collection_name]

    @override
    async def list_collection_names(self, **kwargs) -> Sequence[str]:
        try:
            database = await self._get_database_proxy()
            containers = database.list_containers()
            return [container["id"] async for container in containers]
        except Exception as e:
            raise VectorStoreOperationException("Failed to list collection names.") from e

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager."""
        if self.managed_client:
            await self.cosmos_client.close()
