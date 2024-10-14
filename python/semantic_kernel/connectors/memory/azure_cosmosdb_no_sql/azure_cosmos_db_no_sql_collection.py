# Copyright (c) Microsoft. All rights reserved.

import asyncio
import sys
from collections.abc import Sequence
from typing import Any, TypeVar

from semantic_kernel.connectors.memory.azure_cosmosdb_no_sql.azure_cosmos_db_no_sql_composite_key import (
    AzureCosmosDBNoSQLCompositeKey,
)
from semantic_kernel.connectors.memory.azure_cosmosdb_no_sql.utils import (
    create_default_indexing_policy,
    create_default_vector_embedding_policy,
    get_partition_key,
)
from semantic_kernel.exceptions.memory_connector_exceptions import (
    MemoryConnectorException,
    MemoryConnectorResourceNotFound,
)
from semantic_kernel.kernel_types import OneOrMany

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from azure.cosmos.aio import ContainerProxy, CosmosClient, DatabaseProxy
from azure.cosmos.partition_key import PartitionKey
from azure.identity import DefaultAzureCredential
from pydantic import ValidationError

from semantic_kernel.connectors.memory.azure_cosmosdb_no_sql.azure_cosmos_db_no_sql_settings import (
    AzureCosmosDBNoSQLSettings,
)
from semantic_kernel.data.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_store_record_collection import VectorStoreRecordCollection
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError
from semantic_kernel.utils.experimental_decorator import experimental_class

TModel = TypeVar("TModel")
TKey = TypeVar("TKey", str, AzureCosmosDBNoSQLCompositeKey)


@experimental_class
class AzureCosmosDBNoSQLCollection(VectorStoreRecordCollection[TKey, TModel]):
    """An Azure Cosmos DB NoSQL collection stores documents in a Azure Cosmos DB NoSQL account."""

    cosmos_client: CosmosClient | None
    database_name: str | None
    database_proxy: DatabaseProxy | None
    container_proxy: ContainerProxy | None
    partition_key: PartitionKey | None

    def __init__(
        self,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition,
        collection_name: str,
        url: str | None = None,
        key: str | None = None,
        database_name: str | None = None,
        database_proxy: DatabaseProxy = None,
        cosmos_client: CosmosClient = None,
    ):
        """Initializes a new instance of the AzureCosmosDBNoSQLCollection class.

        Args:
            data_model_type (type[TModel]): The type of the data model.
            data_model_definition (VectorStoreRecordDefinition): The definition of the data model.
            collection_name (str): The name of the collection.
            url (str): The URL of the Azure Cosmos DB NoSQL account. Defaults to None.
            key (str): The key of the Azure Cosmos DB NoSQL account. Defaults to None.
            database_name (str): The name of the database. Used to create a database proxy if not provided.
                                 Defaults to None.
            database_proxy (DatabaseProxy): A custom database proxy. Used to create a container proxy.
                                            Defaults to None.
            cosmos_client (CosmosClient): A custom Cosmos client. Used to create a database proxy if
                                          not provided. Defaults to None.
        """
        if not database_proxy and not database_name:
            raise ServiceInitializationError("database_name is required if database_proxy is not provided.")

        if not database_proxy and not cosmos_client:
            try:
                cosmos_db_nosql_settings = AzureCosmosDBNoSQLSettings.create(url=url, key=key)
            except ValidationError as e:
                raise ServiceInitializationError("Failed to validate Azure Cosmos DB NoSQL settings.") from e

            if cosmos_db_nosql_settings.key:
                cosmos_client = CosmosClient(url, credential=key)
            else:
                cosmos_client = CosmosClient(url, DefaultAzureCredential())

        if database_proxy and cosmos_client:
            raise ServiceInitializationError(
                "Both database_proxy and cosmos_client are provided. Only one of them should be provided."
            )

        super().__init__(
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            collection_name=collection_name,
            database_name=database_name,
            database_proxy=database_proxy,
            cosmos_client=cosmos_client,
        )

    @override
    async def _inner_upsert(
        self,
        records: Sequence[Any],
        **kwargs: Any,
    ) -> Sequence[TKey]:
        pass

    @override
    async def _inner_get(self, keys: Sequence[TKey], **kwargs: Any) -> OneOrMany[Any] | None:
        if not self.container_proxy:
            raise MemoryConnectorResourceNotFound("Container proxy is not initialized.")

        async with self.cosmos_client:
            try:
                results = await asyncio.gather(*[
                    self.container_proxy.read_item(key, partition_key=get_partition_key(key)) for key in keys
                ])
            except Exception as e:
                raise MemoryConnectorException("Failed to read items.") from e

            return results

    @override
    async def _inner_delete(self, keys: Sequence[TKey], **kwargs: Any) -> None:
        pass

    @override
    def _serialize_dicts_to_store_models(self, records: Sequence[dict[str, Any]], **kwargs: Any) -> Sequence[Any]:
        pass

    @override
    def _deserialize_store_models_to_dicts(self, records: Sequence[Any], **kwargs: Any) -> Sequence[dict[str, Any]]:
        pass

    @override
    async def create_collection(self, **kwargs) -> None:
        if self.container_proxy:
            raise MemoryConnectorException("Container proxy is already initialized.")

        async with self.cosmos_client:
            if not self.database_proxy:
                try:
                    self.database_proxy = await self.cosmos_client.create_database_if_not_exists(id=self.database_name)
                except Exception as e:
                    raise MemoryConnectorException("Failed to create database.") from e

            self.partition_key = kwargs.pop(
                "partition_key", PartitionKey(path=f"/{self.data_model_definition.key_field_name}")
            )
            try:
                self.container_proxy = await self.database_proxy.create_container_if_not_exists(
                    id=self.collection_name,
                    partition_key=self.partition_key,
                    indexing_policy=kwargs.pop(
                        "indexing_policy", create_default_indexing_policy(self.data_model_definition)
                    ),
                    vector_embedding_policy=kwargs.pop(
                        "vector_embedding_policy", create_default_vector_embedding_policy(self.data_model_definition)
                    ),
                    **kwargs,
                )
            except Exception as e:
                raise MemoryConnectorException("Failed to create container.") from e

    @override
    async def does_collection_exist(self, **kwargs) -> bool:
        if not self.database_proxy:
            raise MemoryConnectorResourceNotFound("Database proxy is not initialized.")

        if self.container_proxy:
            return True

        async with self.cosmos_client:
            try:
                containers = await self.database_proxy.query_containers(
                    query="SELECT * FROM c WHERE c.id = @id",
                    parameters=[{"name": "@id", "value": self.collection_name}],
                )
            except Exception as e:
                raise MemoryConnectorException("Failed to query containers.") from e

            async for container in containers:
                if container["id"] == self.collection_name:
                    return True

        return False

    @override
    async def delete_collection(self, **kwargs) -> None:
        if not self.container_proxy:
            raise MemoryConnectorResourceNotFound("Container proxy is not initialized.")

        async with self.cosmos_client:
            try:
                await self.database_proxy.delete_container(self.collection_name)
            except Exception as e:
                raise MemoryConnectorException("Failed to delete container.") from e

        self.container_proxy = None
