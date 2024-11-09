# Copyright (c) Microsoft. All rights reserved.

import asyncio
import sys
from collections.abc import Sequence
from typing import Any, TypeVar

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from azure.cosmos.aio import CosmosClient
from azure.cosmos.exceptions import CosmosBatchOperationError, CosmosHttpResponseError, CosmosResourceNotFoundError
from azure.cosmos.partition_key import PartitionKey

from semantic_kernel.connectors.memory.azure_cosmos_db.azure_cosmos_db_no_sql_base import AzureCosmosDBNoSQLBase
from semantic_kernel.connectors.memory.azure_cosmos_db.azure_cosmos_db_no_sql_composite_key import (
    AzureCosmosDBNoSQLCompositeKey,
)
from semantic_kernel.connectors.memory.azure_cosmos_db.const import COSMOS_ITEM_ID_PROPERTY_NAME
from semantic_kernel.connectors.memory.azure_cosmos_db.utils import (
    build_query_parameters,
    create_default_indexing_policy,
    create_default_vector_embedding_policy,
    get_key,
    get_partition_key,
)
from semantic_kernel.data.record_definition.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.vector_storage.vector_store_record_collection import VectorStoreRecordCollection
from semantic_kernel.exceptions.memory_connector_exceptions import (
    MemoryConnectorException,
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

    partition_key: PartitionKey

    def __init__(
        self,
        data_model_type: type[TModel],
        database_name: str,
        collection_name: str,
        data_model_definition: VectorStoreRecordDefinition | None = None,
        url: str | None = None,
        key: str | None = None,
        cosmos_client: CosmosClient | None = None,
        partition_key: PartitionKey | str | None = None,
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
            cosmos_client (CosmosClient): The custom Azure Cosmos DB NoSQL client whose lifetime is managed by the user.
            partition_key (PartitionKey | str): The partition key. Defaults to None. If not provided, the partition
                                                key will be based on the key field of the data model definition.
                                                https://learn.microsoft.com/en-us/azure/cosmos-db/partitioning-overview
            create_database (bool): Indicates whether to create the database if it does not exist.
                                    Defaults to False.
        """
        if not partition_key:
            partition_key = PartitionKey(path=f"/{COSMOS_ITEM_ID_PROPERTY_NAME}")
        else:
            if isinstance(partition_key, str):
                partition_key = PartitionKey(path=f"/{partition_key.strip('/')}")

        super().__init__(
            partition_key=partition_key,
            database_name=database_name,
            url=url,
            key=key,
            cosmos_client=cosmos_client,
            create_database=create_database,
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            collection_name=collection_name,
            managed_client=cosmos_client is None,
        )

    @override
    async def _inner_upsert(
        self,
        records: Sequence[Any],
        **kwargs: Any,
    ) -> Sequence[AzureCosmosDBNoSQLCompositeKey]:
        batch_operations = [("upsert", (record,)) for record in records]
        partition_key = [record[self.partition_key.path.strip("/")] for record in records]
        try:
            container_proxy = await self._get_container_proxy(self.collection_name, **kwargs)
            results = await container_proxy.execute_item_batch(batch_operations, partition_key, **kwargs)
            return [
                AzureCosmosDBNoSQLCompositeKey.from_record(result["resourceBody"], self.partition_key)
                for result in results
            ]
        except CosmosResourceNotFoundError as e:
            raise MemoryConnectorResourceNotFound(
                "The collection does not exist yet. Create the collection first."
            ) from e
        except (CosmosBatchOperationError, CosmosHttpResponseError) as e:
            raise MemoryConnectorException("Failed to upsert items.") from e

    @override
    async def _inner_get(self, keys: Sequence[TKey], **kwargs: Any) -> OneOrMany[Any] | None:
        include_vectors = kwargs.pop("include_vectors", False)
        query, parameters = build_query_parameters(self.data_model_definition, keys, include_vectors)

        try:
            container_proxy = await self._get_container_proxy(self.collection_name, **kwargs)
            results = container_proxy.query_items(query=query, parameters=parameters)
            return [item async for item in results]
        except CosmosResourceNotFoundError as e:
            raise MemoryConnectorResourceNotFound(
                "The collection does not exist yet. Create the collection first."
            ) from e
        except Exception as e:
            raise MemoryConnectorException("Failed to read items.") from e

    @override
    async def _inner_delete(self, keys: Sequence[TKey], **kwargs: Any) -> None:
        container_proxy = await self._get_container_proxy(self.collection_name, **kwargs)
        results = await asyncio.gather(
            *[container_proxy.delete_item(item=get_key(key), partition_key=get_partition_key(key)) for key in keys],
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
        try:
            database_proxy = await self._get_database_proxy(**kwargs)
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
        except CosmosHttpResponseError as e:
            raise MemoryConnectorException("Failed to create container.") from e

    @override
    async def does_collection_exist(self, **kwargs) -> bool:
        try:
            container_proxy = await self._get_container_proxy(self.collection_name, **kwargs)
            await container_proxy.read(**kwargs)
            return True
        except CosmosHttpResponseError:
            return False

    @override
    async def delete_collection(self, **kwargs) -> None:
        try:
            database_proxy = await self._get_database_proxy(**kwargs)
            await database_proxy.delete_container(self.collection_name)
        except CosmosHttpResponseError as e:
            raise MemoryConnectorException("Container could not be deleted.") from e

    @override
    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """Exit the context manager."""
        if self.managed_client:
            await self.cosmos_client.close()
