# Copyright (c) Microsoft. All rights reserved.

import asyncio
import sys
from collections.abc import Sequence
from typing import Any, TypeVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from azure.cosmos.exceptions import CosmosResourceNotFoundError
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
    COSMOS_ITEM_ID_PROPERTY_NAME,
    build_query_parameters,
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


@experimental_class
class AzureCosmosDBNoSQLCollection(AzureCosmosDBNoSQLBase, VectorStoreRecordCollection[TKey, TModel]):
    """An Azure Cosmos DB NoSQL collection stores documents in a Azure Cosmos DB NoSQL account."""

    partition_key: PartitionKey | None

    def __init__(
        self,
        data_model_type: type[TModel],
        database_name: str,
        collection_name: str,
        data_model_definition: VectorStoreRecordDefinition | None = None,
        url: str | None = None,
        key: str | None = None,
        partition_key: PartitionKey | None = None,
        create_database: bool = False,
    ):
        """Initializes a new instance of the AzureCosmosDBNoSQLCollection class.

        Args:
            data_model_type (type[TModel]): The type of the data model.
            database_name (str): The name of the database. Used to create a database proxy if not provided.
            collection_name (str): The name of the collection.
            data_model_definition (VectorStoreRecordDefinition): The definition of the data model. Defaults to None.
            url (str): The URL of the Azure Cosmos DB NoSQL account. Defaults to None.
            key (str): The key of the Azure Cosmos DB NoSQL account. Defaults to None.
            partition_key (PartitionKey): The partition key. Defaults to None. If not provided, the partition
                                          key will be based on the key field of the data model definition.
            create_database (bool): Indicates whether to create the database if it does not exist.
                                    Defaults to False.
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
            partition_key=partition_key,
            create_database=create_database,
        )

        # data_model_definition may not be available until the base class is initialized
        self.partition_key = self.partition_key or PartitionKey(path=f"/{self.data_model_definition.key_field_name}")

    @override
    async def _inner_upsert(
        self,
        records: Sequence[Any],
        **kwargs: Any,
    ) -> Sequence[TKey]:
        async with self._get_cosmos_client() as cosmos_client:
            try:
                container_proxy = await self._get_container_proxy(self.collection_name, cosmos_client)
                results = await asyncio.gather(*[container_proxy.upsert_item(body=record) for record in records])
            except Exception as e:
                raise MemoryConnectorException("Failed to upsert items.") from e

            return [result[COSMOS_ITEM_ID_PROPERTY_NAME] for result in results]

    @override
    async def _inner_get(self, keys: Sequence[TKey], **kwargs: Any) -> OneOrMany[Any] | None:
        include_vectors = kwargs.pop("include_vectors", False)

        async with self._get_cosmos_client() as cosmos_client:
            try:
                container_proxy = await self._get_container_proxy(self.collection_name, cosmos_client)
            except CosmosResourceNotFoundError as e:
                raise MemoryConnectorResourceNotFound(
                    "The collection does not exist yet. Create the collection first."
                ) from e

            try:
                query, parameters = build_query_parameters(self.data_model_definition, keys, include_vectors)
                results = container_proxy.query_items(query=query, parameters=parameters)
                return [item async for item in results]
            except Exception as e:
                raise MemoryConnectorException("Failed to read items.") from e

    @override
    async def _inner_delete(self, keys: Sequence[TKey], **kwargs: Any) -> None:
        async with self._get_cosmos_client() as cosmos_client:
            try:
                container_proxy = await self._get_container_proxy(self.collection_name, cosmos_client)
            except CosmosResourceNotFoundError as e:
                raise MemoryConnectorResourceNotFound(
                    "The collection does not exist yet. Create the collection first."
                ) from e

            results = await asyncio.gather(
                *[container_proxy.delete_item(item=key, partition_key=get_partition_key(key)) for key in keys],
                return_exceptions=True,
            )

            exceptions = [result for result in results if isinstance(result, Exception)]
            if exceptions:
                raise MemoryConnectorException("Failed to delete item(s).", exceptions)

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
                database_proxy = await self._get_database_proxy(cosmos_client)
                await database_proxy.create_container_if_not_exists(
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
        async with self._get_cosmos_client() as cosmos_client:
            try:
                database = await self._get_database_proxy(cosmos_client)
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
            try:
                database_proxy = await self._get_database_proxy(cosmos_client)
                await database_proxy.delete_container(self.collection_name)
            except CosmosResourceNotFoundError as e:
                raise MemoryConnectorResourceNotFound(
                    "Collection does not exist yet. Create the collection first."
                ) from e
            except Exception as e:
                raise MemoryConnectorException("Failed to delete container.") from e
