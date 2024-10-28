# Copyright (c) Microsoft. All rights reserved.

from typing import Any

import pytest
from azure.cosmos.partition_key import PartitionKey

from semantic_kernel.connectors.memory.azure_cosmosdb_no_sql.azure_cosmos_db_no_sql_composite_key import (
    AzureCosmosDBNoSQLCompositeKey,
)
from semantic_kernel.data.vector_store import VectorStore
from semantic_kernel.exceptions.memory_connector_exceptions import MemoryConnectorException
from tests.integration.memory.vector_stores.vector_store_test_base import VectorStoreTestBase


class TestCosmosDBNoSQL(VectorStoreTestBase):
    """Test Cosmos DB NoSQL store functionality."""

    @pytest.mark.asyncio
    async def test_list_collection_names(
        self,
        stores: dict[str, VectorStore],
        data_model_type: type,
    ):
        """Test list collection names."""
        store = stores["azure_cosmos_db_nosql"]

        assert await store.list_collection_names() == []

        collection_name = "list_collection_names"
        collection = store.get_collection(collection_name, data_model_type)
        await collection.create_collection()

        collection_names = await store.list_collection_names()
        assert collection_name in collection_names

        await collection.delete_collection()
        assert await collection.does_collection_exist() is False
        collection_names = await store.list_collection_names()
        assert collection_name not in collection_names

        # Deleting the collection doesn't remove it from the vector_record_collections list in the store
        assert collection_name in store.vector_record_collections

    @pytest.mark.asyncio
    async def test_collection_not_created(
        self,
        stores: dict[str, VectorStore],
        data_model_type: type,
        data_record: dict[str, Any],
    ):
        """Test get without collection."""
        store = stores["azure_cosmos_db_nosql"]
        collection_name = "collection_not_created"
        collection = store.get_collection(collection_name, data_model_type)

        assert await collection.does_collection_exist() is False

        with pytest.raises(
            MemoryConnectorException, match="The collection does not exist yet. Create the collection first."
        ):
            await collection.upsert(data_model_type(**data_record))

        with pytest.raises(
            MemoryConnectorException, match="The collection does not exist yet. Create the collection first."
        ):
            await collection.get(data_record["id"])

        with pytest.raises(MemoryConnectorException):
            await collection.delete(data_record["id"])

        with pytest.raises(
            MemoryConnectorException, match="The collection does not exist yet. Create the collection first."
        ):
            await collection.delete_collection()

    @pytest.mark.asyncio
    async def test_custom_partition_key(
        self,
        stores: dict[str, VectorStore],
        data_model_type: type,
        data_record: dict[str, Any],
    ):
        """Test custom partition key."""
        store = stores["azure_cosmos_db_nosql"]
        collection_name = "custom_partition_key"
        collection = store.get_collection(
            collection_name,
            data_model_type,
            partition_key=PartitionKey(path="/product_type"),
        )

        composite_key = AzureCosmosDBNoSQLCompositeKey(key=data_record["id"], partition_key=data_record["product_type"])

        # Upsert
        await collection.create_collection()
        await collection.upsert(data_model_type(**data_record))

        # Verify
        record = await collection.get(composite_key)
        assert record is not None
        assert isinstance(record, data_model_type)

        # Remove
        await collection.delete(composite_key)
        record = await collection.get(composite_key)
        assert record is None

        # Remove collection
        await collection.delete_collection()
        assert await collection.does_collection_exist() is False

    @pytest.mark.asyncio
    async def test_get_include_vector(
        self,
        stores: dict[str, VectorStore],
        data_model_type: type,
        data_record: dict[str, Any],
    ):
        """Test get with include_vector."""
        store = stores["azure_cosmos_db_nosql"]
        collection_name = "get_include_vector"
        collection = store.get_collection(collection_name, data_model_type)

        # Upsert
        await collection.create_collection()
        await collection.upsert(data_model_type(**data_record))

        # Verify
        record = await collection.get(data_record["id"], include_vectors=True)
        assert record is not None
        assert isinstance(record, data_model_type)
        assert record.vector == data_record["vector"]

        # Remove
        await collection.delete(data_record["id"])
        record = await collection.get(data_record["id"])
        assert record is None

        # Remove collection
        await collection.delete_collection()
        assert await collection.does_collection_exist() is False

    @pytest.mark.asyncio
    async def test_get_not_include_vector(
        self,
        stores: dict[str, VectorStore],
        data_model_type: type,
        data_record: dict[str, Any],
    ):
        """Test get with include_vector."""
        store = stores["azure_cosmos_db_nosql"]
        collection_name = "get_not_include_vector"
        collection = store.get_collection(collection_name, data_model_type)

        # Upsert
        await collection.create_collection()
        await collection.upsert(data_model_type(**data_record))

        # Verify
        record = await collection.get(data_record["id"], include_vectors=False)
        assert record is not None
        assert isinstance(record, data_model_type)
        assert record.vector is None

        # Remove
        await collection.delete(data_record["id"])
        record = await collection.get(data_record["id"])
        assert record is None

        # Remove collection
        await collection.delete_collection()
        assert await collection.does_collection_exist() is False

    @pytest.mark.asyncio
    async def test_collection_with_key_as_key_field(
        self,
        stores: dict[str, VectorStore],
        data_model_type_with_key_as_key_field: type,
        data_record_with_key_as_key_field: dict[str, Any],
    ):
        """Test collection with key as key field."""
        store = stores["azure_cosmos_db_nosql"]
        collection_name = "collection_with_key_as_key_field"
        collection = store.get_collection(collection_name, data_model_type_with_key_as_key_field)

        # Upsert
        await collection.create_collection()
        results = await collection.upsert(data_model_type_with_key_as_key_field(**data_record_with_key_as_key_field))
        assert data_record_with_key_as_key_field["key"] in results

        # Verify
        record = await collection.get(data_record_with_key_as_key_field["key"])
        assert record is not None
        assert isinstance(record, data_model_type_with_key_as_key_field)
        assert record.key == data_record_with_key_as_key_field["key"]

        # Remove
        await collection.delete(data_record_with_key_as_key_field["key"])
        record = await collection.get(data_record_with_key_as_key_field["key"])
        assert record is None

        # Remove collection
        await collection.delete_collection()
        assert await collection.does_collection_exist() is False
