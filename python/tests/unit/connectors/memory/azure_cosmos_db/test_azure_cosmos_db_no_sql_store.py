# Copyright (c) Microsoft. All rights reserved.


from unittest.mock import patch

import pytest

from semantic_kernel.connectors.memory.azure_cosmos_db.azure_cosmos_db_no_sql_collection import (
    AzureCosmosDBNoSQLCollection,
)
from semantic_kernel.connectors.memory.azure_cosmos_db.azure_cosmos_db_no_sql_store import AzureCosmosDBNoSQLStore
from semantic_kernel.connectors.memory.azure_cosmos_db.utils import CosmosClientWrapper
from semantic_kernel.exceptions import VectorStoreInitializationException


def test_azure_cosmos_db_no_sql_store_init(
    clear_azure_cosmos_db_no_sql_env,
    database_name: str,
    url: str,
    key: str,
) -> None:
    """Test the initialization of an AzureCosmosDBNoSQLStore object."""
    vector_store = AzureCosmosDBNoSQLStore(url=url, key=key, database_name=database_name)

    assert vector_store is not None
    assert vector_store.database_name == database_name
    assert vector_store.cosmos_client is not None
    assert vector_store.create_database is False


def test_azure_cosmos_db_no_sql_store_init_env(azure_cosmos_db_no_sql_unit_test_env) -> None:
    """Test the initialization of an AzureCosmosDBNoSQLStore object with environment variables."""
    vector_store = AzureCosmosDBNoSQLStore()

    assert vector_store is not None
    assert vector_store.database_name == azure_cosmos_db_no_sql_unit_test_env["AZURE_COSMOS_DB_NO_SQL_DATABASE_NAME"]
    assert vector_store.cosmos_client is not None
    assert vector_store.create_database is False


@pytest.mark.parametrize("exclude_list", [["AZURE_COSMOS_DB_NO_SQL_URL"]], indirect=True)
def test_azure_cosmos_db_no_sql_store_init_no_url(
    azure_cosmos_db_no_sql_unit_test_env,
) -> None:
    """Test the initialization of an AzureCosmosDBNoSQLStore object with missing URL."""
    with pytest.raises(VectorStoreInitializationException):
        AzureCosmosDBNoSQLStore(env_file_path="fake_path")


@pytest.mark.parametrize("exclude_list", [["AZURE_COSMOS_DB_NO_SQL_DATABASE_NAME"]], indirect=True)
def test_azure_cosmos_db_no_sql_store_init_no_database_name(
    azure_cosmos_db_no_sql_unit_test_env,
) -> None:
    """Test the initialization of an AzureCosmosDBNoSQLStore object with missing database name."""
    with pytest.raises(
        VectorStoreInitializationException, match="The name of the Azure Cosmos DB NoSQL database is missing."
    ):
        AzureCosmosDBNoSQLStore(env_file_path="fake_path")


def test_azure_cosmos_db_no_sql_store_invalid_settings(
    clear_azure_cosmos_db_no_sql_env,
) -> None:
    """Test the initialization of an AzureCosmosDBNoSQLStore object with invalid settings."""
    with pytest.raises(VectorStoreInitializationException, match="Failed to validate Azure Cosmos DB NoSQL settings."):
        AzureCosmosDBNoSQLStore(url="invalid_url")


@patch.object(AzureCosmosDBNoSQLCollection, "__init__", return_value=None)
def test_azure_cosmos_db_no_sql_store_get_collection(
    mock_azure_cosmos_db_no_sql_collection_init,
    azure_cosmos_db_no_sql_unit_test_env,
    collection_name: str,
    data_model_type,
) -> None:
    """Test the get_collection method of an AzureCosmosDBNoSQLStore object."""
    vector_store = AzureCosmosDBNoSQLStore()

    # Before calling get_collection, the collection should not exist.
    assert vector_store.vector_record_collections.get(collection_name) is None

    collection = vector_store.get_collection(collection_name=collection_name, data_model_type=data_model_type)

    assert collection is not None
    assert vector_store.vector_record_collections.get(collection_name) is not None
    mock_azure_cosmos_db_no_sql_collection_init.assert_called_once_with(
        data_model_type,
        collection_name,
        database_name=azure_cosmos_db_no_sql_unit_test_env["AZURE_COSMOS_DB_NO_SQL_DATABASE_NAME"],
        data_model_definition=None,
        cosmos_client=vector_store.cosmos_client,
        create_database=vector_store.create_database,
        env_file_path=vector_store.cosmos_db_nosql_settings.env_file_path,
        env_file_encoding=vector_store.cosmos_db_nosql_settings.env_file_encoding,
    )


@patch.object(CosmosClientWrapper, "close", return_value=None)
async def test_client_is_closed(mock_cosmos_client_close, azure_cosmos_db_no_sql_unit_test_env) -> None:
    """Test the close method of an AzureCosmosDBNoSQLStore object."""
    async with AzureCosmosDBNoSQLStore() as vector_store:
        assert vector_store.cosmos_client is not None

    mock_cosmos_client_close.assert_called()
