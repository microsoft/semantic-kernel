# Copyright (c) Microsoft. All rights reserved.

import os
import platform
from collections.abc import Callable
from typing import Any

import pytest
from azure.cosmos.aio import CosmosClient
from azure.cosmos.partition_key import PartitionKey

from semantic_kernel.connectors.memory.azure_cosmos_db.azure_cosmos_db_no_sql_composite_key import (
    AzureCosmosDBNoSQLCompositeKey,
)
from semantic_kernel.connectors.memory.azure_cosmos_db.azure_cosmos_db_no_sql_store import AzureCosmosDBNoSQLStore
from semantic_kernel.data.vector_storage import VectorStore
from semantic_kernel.exceptions.memory_connector_exceptions import MemoryConnectorException
from tests.integration.memory.vector_stores.vector_store_test_base import VectorStoreTestBase


@pytest.mark.skipif(
    platform.system() != "Windows",
    reason="The Azure Cosmos DB Emulator is only available on Windows.",
)
class TestCosmosDBNoSQL(VectorStoreTestBase):
    """Test Cosmos DB NoSQL store functionality."""

    async def test_list_collection_names(
        self,
        stores: dict[str, Callable[[], VectorStore]],
        data_model_type: type,
    ):
        """Test list collection names."""
        async with stores["azure_cosmos_db_no_sql"]() as store:
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

    async def test_collection_not_created(
        self,
        stores: dict[str, Callable[[], VectorStore]],
        data_model_type: type,
        data_record: dict[str, Any],
    ):
        """Test get without collection."""
        async with stores["azure_cosmos_db_no_sql"]() as store:
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

            with pytest.raises(MemoryConnectorException, match="Container could not be deleted."):
                await collection.delete_collection()

    async def test_custom_partition_key(
        self,
        stores: dict[str, Callable[[], VectorStore]],
        data_model_type: type,
        data_record: dict[str, Any],
    ):
        """Test custom partition key."""
        async with stores["azure_cosmos_db_no_sql"]() as store:
            collection_name = "custom_partition_key"
            collection = store.get_collection(
                collection_name,
                data_model_type,
                partition_key=PartitionKey(path="/product_type"),
            )

            composite_key = AzureCosmosDBNoSQLCompositeKey(
                key=data_record["id"], partition_key=data_record["product_type"]
            )

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

    async def test_get_include_vector(
        self,
        stores: dict[str, Callable[[], VectorStore]],
        data_model_type: type,
        data_record: dict[str, Any],
    ):
        """Test get with include_vector."""
        async with stores["azure_cosmos_db_no_sql"]() as store:
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

    async def test_get_not_include_vector(
        self,
        stores: dict[str, Callable[[], VectorStore]],
        data_model_type: type,
        data_record: dict[str, Any],
    ):
        """Test get with include_vector."""
        async with stores["azure_cosmos_db_no_sql"]() as store:
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

    async def test_collection_with_key_as_key_field(
        self,
        stores: dict[str, Callable[[], VectorStore]],
        data_model_type_with_key_as_key_field: type,
        data_record_with_key_as_key_field: dict[str, Any],
    ):
        """Test collection with key as key field."""
        async with stores["azure_cosmos_db_no_sql"]() as store:
            collection_name = "collection_with_key_as_key_field"
            collection = store.get_collection(collection_name, data_model_type_with_key_as_key_field)

            # Upsert
            await collection.create_collection()
            result = await collection.upsert(data_model_type_with_key_as_key_field(**data_record_with_key_as_key_field))
            assert data_record_with_key_as_key_field["key"] == result

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

    async def test_custom_client(
        self,
        data_model_type: type,
    ):
        """Test list collection names."""
        url = os.environ.get("AZURE_COSMOS_DB_NO_SQL_URL")
        key = os.environ.get("AZURE_COSMOS_DB_NO_SQL_KEY")

        async with (
            CosmosClient(url, key) as custom_client,
            AzureCosmosDBNoSQLStore(
                database_name="test_database",
                cosmos_client=custom_client,
                create_database=True,
            ) as store,
        ):
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
