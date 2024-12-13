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
    create_default_indexing_policy,
    create_default_vector_embedding_policy,
    get_key,
    get_partition_key,
)
from semantic_kernel.data.filter_clauses.any_tags_equal_to_filter_clause import AnyTagsEqualTo
from semantic_kernel.data.filter_clauses.equal_to_filter_clause import EqualTo
from semantic_kernel.data.kernel_search_results import KernelSearchResults
from semantic_kernel.data.record_definition.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.record_definition.vector_store_record_fields import VectorStoreRecordDataField
from semantic_kernel.data.vector_search.vector_search import VectorSearchBase
from semantic_kernel.data.vector_search.vector_search_filter import VectorSearchFilter
from semantic_kernel.data.vector_search.vector_search_options import VectorSearchOptions
from semantic_kernel.data.vector_search.vector_search_result import VectorSearchResult
from semantic_kernel.data.vector_search.vector_text_search import VectorTextSearchMixin
from semantic_kernel.data.vector_search.vectorized_search import VectorizedSearchMixin
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
class AzureCosmosDBNoSQLCollection(
    AzureCosmosDBNoSQLBase,
    VectorSearchBase[TKey, TModel],
    VectorizedSearchMixin[TModel],
    VectorTextSearchMixin[TModel],
):
    """An Azure Cosmos DB NoSQL collection stores documents in a Azure Cosmos DB NoSQL account."""

    partition_key: PartitionKey

    def __init__(
        self,
        data_model_type: type[TModel],
        collection_name: str,
        database_name: str | None = None,
        data_model_definition: VectorStoreRecordDefinition | None = None,
        url: str | None = None,
        key: str | None = None,
        cosmos_client: CosmosClient | None = None,
        partition_key: PartitionKey | str | None = None,
        create_database: bool = False,
        env_file_path: str | None = None,
        env_file_encoding: str | None = None,
    ):
        """Initializes a new instance of the AzureCosmosDBNoSQLCollection class.

        Args:
            data_model_type (type[TModel]): The type of the data model.
            collection_name (str): The name of the collection.
            database_name (str): The name of the database. Used to create a database proxy if not provided.
                                 Defaults to None.
            data_model_definition (VectorStoreRecordDefinition): The definition of the data model. Defaults to None.
            url (str): The URL of the Azure Cosmos DB NoSQL account. Defaults to None.
            key (str): The key of the Azure Cosmos DB NoSQL account. Defaults to None.
            cosmos_client (CosmosClient): The custom Azure Cosmos DB NoSQL client whose lifetime is managed by the user.
            partition_key (PartitionKey | str): The partition key. Defaults to None. If not provided, the partition
                                                key will be based on the key field of the data model definition.
                                                https://learn.microsoft.com/en-us/azure/cosmos-db/partitioning-overview
            create_database (bool): Indicates whether to create the database if it does not exist.
                                    Defaults to False.
            env_file_path (str): The path to the .env file. Defaults to None.
            env_file_encoding (str): The encoding of the .env file. Defaults to None.
        """
        if not partition_key:
            partition_key = PartitionKey(path=f"/{COSMOS_ITEM_ID_PROPERTY_NAME}")
        else:
            if isinstance(partition_key, str):
                partition_key = PartitionKey(path=f"/{partition_key.strip('/')}")

        super().__init__(
            partition_key=partition_key,
            url=url,
            key=key,
            database_name=database_name,
            cosmos_client=cosmos_client,
            create_database=create_database,
            env_file_path=env_file_path,
            env_file_encoding=env_file_encoding,
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
    ) -> Sequence[TKey]:
        container_proxy = await self._get_container_proxy(self.collection_name, **kwargs)
        try:
            results = await asyncio.gather(*(container_proxy.upsert_item(record) for record in records))
            return [result[COSMOS_ITEM_ID_PROPERTY_NAME] for result in results]
        except CosmosResourceNotFoundError as e:
            raise MemoryConnectorResourceNotFound(
                "The collection does not exist yet. Create the collection first."
            ) from e
        except (CosmosBatchOperationError, CosmosHttpResponseError) as e:
            raise MemoryConnectorException("Failed to upsert items.") from e

    @override
    async def _inner_get(self, keys: Sequence[TKey], **kwargs: Any) -> OneOrMany[Any] | None:
        include_vectors = kwargs.pop("include_vectors", False)
        query = (
            f"SELECT {self._build_select_clause(include_vectors)} FROM c WHERE "  # nosec: B608
            f"c.id IN ({', '.join([f'@id{i}' for i in range(len(keys))])})"  # nosec: B608
        )  # nosec: B608
        parameters: list[dict[str, Any]] = [{"name": f"@id{i}", "value": get_key(key)} for i, key in enumerate(keys)]

        container_proxy = await self._get_container_proxy(self.collection_name, **kwargs)
        try:
            return [item async for item in container_proxy.query_items(query=query, parameters=parameters)]
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
    async def _inner_search(
        self,
        options: VectorSearchOptions,
        search_text: str | None = None,
        vectorizable_text: str | None = None,
        vector: list[float | int] | None = None,
        **kwargs: Any,
    ) -> KernelSearchResults[VectorSearchResult[TModel]]:
        params = [{"name": "@top", "value": options.top}]
        if search_text is not None:
            query = self._build_search_text_query(options)
            params.append({"name": "@search_text", "value": search_text})
        elif vector is not None:
            query = self._build_vector_query(options)
            params.append({"name": "@vector", "value": vector})
        else:
            raise ValueError("Either search_text or vector must be provided.")
        container_proxy = await self._get_container_proxy(self.collection_name, **kwargs)
        try:
            results = container_proxy.query_items(query, parameters=params)
        except Exception as e:
            raise MemoryConnectorException("Failed to search items.") from e
        return KernelSearchResults(
            results=self._get_vector_search_results_from_results(results, options),
            total_count=None,
        )

    def _build_search_text_query(self, options: VectorSearchOptions) -> str:
        where_clauses = self._build_where_clauses_from_filter(options.filter)
        contains_clauses = " OR ".join(
            f"CONTAINS(c.{field}, @search_text)"
            for field in self.data_model_definition.fields
            if isinstance(field, VectorStoreRecordDataField) and field.is_full_text_searchable
        )
        return (
            f"SELECT TOP @top {self._build_select_clause(options.include_vectors)} "  # nosec: B608
            f"FROM c WHERE ({contains_clauses}) AND {where_clauses}"  # nosec: B608
        )

    def _build_vector_query(self, options: VectorSearchOptions) -> str:
        where_clauses = self._build_where_clauses_from_filter(options.filter)
        if where_clauses:
            where_clauses = f"WHERE {where_clauses}"
        vector_field_name: str = self.data_model_definition.try_get_vector_field(options.vector_field_name).name  # type: ignore
        return (
            f"SELECT TOP @top {self._build_select_clause(options.include_vectors)},"  # nosec: B608
            f" VectorDistance(c.{vector_field_name}, @vector) AS distance FROM c ORDER "  # nosec: B608
            f"BY VectorDistance(c.{vector_field_name}, @vector) {where_clauses}"  # nosec: B608
        )

    def _build_select_clause(self, include_vectors: bool) -> str:
        """Create the select clause for a CosmosDB query."""
        included_fields = [
            field
            for field in self.data_model_definition.field_names
            if include_vectors or field not in self.data_model_definition.vector_field_names
        ]
        if self.data_model_definition.key_field_name != COSMOS_ITEM_ID_PROPERTY_NAME:
            # Replace the key field name with the Cosmos item id property name
            included_fields = [
                field if field != self.data_model_definition.key_field_name else COSMOS_ITEM_ID_PROPERTY_NAME
                for field in included_fields
            ]

        return ", ".join(f"c.{field}" for field in included_fields)

    def _build_where_clauses_from_filter(self, filters: VectorSearchFilter | None) -> str:
        if filters is None:
            return ""
        clauses = []
        for filter in filters.filters:
            match filter:
                case EqualTo():
                    clauses.append(f"c.{filter.field_name} = {filter.value}")
                case AnyTagsEqualTo():
                    clauses.append(f"{filter.value} IN c.{filter.field_name}")
                case _:
                    raise ValueError(f"Unsupported filter: {filter}")
        return " AND ".join(clauses)

    @override
    def _get_record_from_result(self, result: dict[str, Any]) -> dict[str, Any]:
        return result

    @override
    def _get_score_from_result(self, result: dict[str, Any]) -> float | None:
        return result.get("distance")

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
