# Copyright (c) Microsoft. All rights reserved.


from unittest.mock import patch

import pytest

from semantic_kernel.connectors.memory.azure_cosmos_db.azure_cosmos_db_no_sql_collection import (
    AzureCosmosDBNoSQLCollection,
)
from semantic_kernel.connectors.memory.azure_cosmos_db.azure_cosmos_db_no_sql_store import AzureCosmosDBNoSQLStore
from semantic_kernel.exceptions.memory_connector_exceptions import MemoryConnectorInitializationError


def test_azure_cosmos_db_no_sql_store_init(
    clear_azure_cosmos_db_no_sql_env,
    database_name: str,
    url: str,
    key: str,
) -> None:
    """Test the initialization of an AzureCosmosDBNoSQLStore object."""
    vector_store = AzureCosmosDBNoSQLStore(database_name=database_name, url=url, key=key)

    assert vector_store is not None
    assert vector_store.database_name == database_name
    assert vector_store.cosmos_client is not None
    assert vector_store.create_database is False


def test_azure_cosmos_db_no_sql_store_init_env(azure_cosmos_db_no_sql_unit_test_env, database_name: str) -> None:
    """Test the initialization of an AzureCosmosDBNoSQLStore object with environment variables."""
    vector_store = AzureCosmosDBNoSQLStore(database_name=database_name)

    assert vector_store is not None
    assert vector_store.database_name == database_name
    assert vector_store.cosmos_client is not None
    assert vector_store.create_database is False


def test_azure_cosmos_db_no_sql_store_invalid_settings(
    clear_azure_cosmos_db_no_sql_env,
    database_name: str,
) -> None:
    """Test the initialization of an AzureCosmosDBNoSQLStore object with invalid settings."""
    with pytest.raises(MemoryConnectorInitializationError):
        AzureCosmosDBNoSQLStore(database_name=database_name, url="invalid_url")


@patch.object(AzureCosmosDBNoSQLCollection, "__init__", return_value=None)
def test_azure_cosmos_db_no_sql_store_get_collection(
    mock_azure_cosmos_db_no_sql_collection_init,
    azure_cosmos_db_no_sql_unit_test_env,
    database_name: str,
    collection_name: str,
    data_model_type,
) -> None:
    """Test the get_collection method of an AzureCosmosDBNoSQLStore object."""
    vector_store = AzureCosmosDBNoSQLStore(database_name=database_name)

    # Before calling get_collection, the collection should not exist.
    assert vector_store.vector_record_collections.get(collection_name) is None

    collection = vector_store.get_collection(collection_name=collection_name, data_model_type=data_model_type)

    assert collection is not None
    assert vector_store.vector_record_collections.get(collection_name) is not None
    mock_azure_cosmos_db_no_sql_collection_init.assert_called_once_with(
        data_model_type,
        database_name,
        collection_name,
        data_model_definition=None,
        cosmos_client=vector_store.cosmos_client,
        create_database=vector_store.create_database,
    )
