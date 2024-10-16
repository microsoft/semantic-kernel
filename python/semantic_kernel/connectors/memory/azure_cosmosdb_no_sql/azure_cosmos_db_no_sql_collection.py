# Copyright (c) Microsoft. All rights reserved.

import asyncio
import sys
from collections.abc import Sequence
from typing import Any, TypeVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from azure.cosmos.partition_key import PartitionKey
from pydantic import ValidationError

from semantic_kernel.connectors.memory.azure_cosmosdb_no_sql.azure_cosmos_db_no_sql_base import AzureCosmosDBNoSQLBase
from semantic_kernel.connectors.memory.azure_cosmosdb_no_sql.azure_cosmos_db_no_sql_composite_key import (
    AzureCosmosDBNoSQLCompositeKey,
)
from semantic_kernel.connectors.memory.azure_cosmosdb_no_sql.azure_cosmos_db_no_sql_settings import (
    AzureCosmosDBNoSQLSettings,
)
from semantic_kernel.connectors.memory.azure_cosmosdb_no_sql.utils import (
    create_default_indexing_policy,
    create_default_vector_embedding_policy,
    get_partition_key,
)
from semantic_kernel.data.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_store_record_collection import VectorStoreRecordCollection
from semantic_kernel.exceptions.memory_connector_exceptions import (
    MemoryConnectorException,
    MemoryConnectorInitializationError,
    MemoryConnectorResourceNotFound,
    VectorStoreModelDeserializationException,
)
from semantic_kernel.kernel_types import OneOrMany
from semantic_kernel.utils.experimental_decorator import experimental_class

TModel = TypeVar("TModel")
TKey = TypeVar("TKey", str, AzureCosmosDBNoSQLCompositeKey)

# The name of the property that will be used as the item id in Azure Cosmos DB NoSQL
COSMOS_ITEM_ID_PROPERTY_NAME = "id"


@experimental_class
class AzureCosmosDBNoSQLCollection(AzureCosmosDBNoSQLBase, VectorStoreRecordCollection[TKey, TModel]):
    """An Azure Cosmos DB NoSQL collection stores documents in a Azure Cosmos DB NoSQL account."""

    def __init__(
        self,
        data_model_type: type[TModel],
        data_model_definition: VectorStoreRecordDefinition,
        database_name: str,
        collection_name: str,
        url: str | None = None,
        key: str | None = None,
    ):
        """Initializes a new instance of the AzureCosmosDBNoSQLCollection class.

        Args:
            data_model_type (type[TModel]): The type of the data model.
            data_model_definition (VectorStoreRecordDefinition): The definition of the data model.
            database_name (str): The name of the database. Used to create a database proxy if not provided.
            collection_name (str): The name of the collection.
            url (str): The URL of the Azure Cosmos DB NoSQL account. Defaults to None.
            key (str): The key of the Azure Cosmos DB NoSQL account. Defaults to None.
        """
        try:
            cosmos_db_nosql_settings = AzureCosmosDBNoSQLSettings.create(url=url, key=key)
        except ValidationError as e:
            raise MemoryConnectorInitializationError("Failed to validate Azure Cosmos DB NoSQL settings.") from e

        super().__init__(
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            cosmos_db_nosql_settings=cosmos_db_nosql_settings,
            database_name=database_name,
            collection_name=collection_name,
        )

    @override
    async def _inner_upsert(
        self,
        records: Sequence[Any],
        **kwargs: Any,
    ) -> Sequence[TKey]:
        async with self._get_cosmos_client() as cosmos_client:
            try:
                container_proxy = self._get_container_proxy(self.collection_name, cosmos_client)
                results = await asyncio.gather(*[container_proxy.create_item(body=record) for record in records])
            except Exception as e:
                raise MemoryConnectorException("Failed to upsert items.") from e

            return [result[COSMOS_ITEM_ID_PROPERTY_NAME] for result in results]

    @override
    async def _inner_get(self, keys: Sequence[TKey], **kwargs: Any) -> OneOrMany[Any] | None:
        async with self._get_cosmos_client() as cosmos_client:
            try:
                container_proxy = self._get_container_proxy(self.collection_name, cosmos_client)
                results = await asyncio.gather(*[
                    container_proxy.read_item(item=key, partition_key=get_partition_key(key)) for key in keys
                ])
            except Exception as e:
                raise MemoryConnectorException("Failed to read items.") from e

            return results

    @override
    async def _inner_delete(self, keys: Sequence[TKey], **kwargs: Any) -> None:
        async with self._get_cosmos_client() as cosmos_client:
            try:
                container_proxy = self._get_container_proxy(self.collection_name, cosmos_client)
                await asyncio.gather(*[
                    container_proxy.delete_item(item=key, partition_key=get_partition_key(key)) for key in keys
                ])
            except Exception as e:
                raise MemoryConnectorException("Failed to delete items.") from e

    @override
    def _serialize_dicts_to_store_models(self, records: Sequence[dict[str, Any]], **kwargs: Any) -> Sequence[Any]:
        serialized_records = []

        key_field_name = self.data_model_definition.key_field_name
        for record in records:
            if key_field_name not in record:
                # The id property will be automatically generated by Azure Cosmos DB NoSQL if not provided
                # https://learn.microsoft.com/en-us/azure/cosmos-db/resource-model#properties-of-an-item
                serialized_record = record
            else:
                serialized_record = {**record, COSMOS_ITEM_ID_PROPERTY_NAME: record[key_field_name]}
                if key_field_name != COSMOS_ITEM_ID_PROPERTY_NAME:
                    # Remove the key field from the serialized record
                    serialized_record.pop(key_field_name, None)

            serialized_records.append(serialized_record)

        return serialized_records

    @override
    def _deserialize_store_models_to_dicts(self, records: Sequence[Any], **kwargs: Any) -> Sequence[dict[str, Any]]:
        deserialized_records = []

        key_field_name = self.data_model_definition.key_field_name
        for record in records:
            if COSMOS_ITEM_ID_PROPERTY_NAME not in record:
                raise VectorStoreModelDeserializationException(
                    f"The record does not have the {COSMOS_ITEM_ID_PROPERTY_NAME} property."
                )

            deserialized_record = {**record, key_field_name: record[COSMOS_ITEM_ID_PROPERTY_NAME]}
            if key_field_name != COSMOS_ITEM_ID_PROPERTY_NAME:
                # Remove the id property from the deserialized record
                deserialized_record.pop(COSMOS_ITEM_ID_PROPERTY_NAME, None)

            deserialized_records.append(deserialized_record)

        return deserialized_records

    @override
    async def create_collection(self, **kwargs) -> None:
        async with self._get_cosmos_client() as cosmos_client:
            try:
                database_proxy = await cosmos_client.create_database_if_not_exists(id=self.database_name)
                await database_proxy.create_container_if_not_exists(
                    id=self.collection_name,
                    partition_key=kwargs.pop(
                        "partition_key", PartitionKey(path=f"/{self.data_model_definition.key_field_name}")
                    ),
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
        async with self._get_cosmos_client() as cosmos_client:
            if not await self._does_database_exist(cosmos_client):
                raise MemoryConnectorResourceNotFound(f"Database '{self.database_name}' does not exist.")

            try:
                database = self._get_database_proxy(self.database_name, cosmos_client)
                containers = database.query_containers(
                    query="SELECT * FROM c WHERE c.id = @id",
                    parameters=[{"name": "@id", "value": self.collection_name}],
                )

                async for container in containers:
                    if container["id"] == self.collection_name:
                        return True
            except Exception as e:
                raise MemoryConnectorException("Failed to query containers.") from e

        return False

    @override
    async def delete_collection(self, **kwargs) -> None:
        async with self._get_cosmos_client() as cosmos_client:
            if not await self._does_database_exist(cosmos_client):
                raise MemoryConnectorResourceNotFound(f"Database '{self.database_name}' does not exist.")

            try:
                database_proxy = await self._get_database_proxy(self.database_name, cosmos_client)
                await database_proxy.delete_container(self.collection_name)
            except Exception as e:
                raise MemoryConnectorException("Failed to delete container.") from e
