# Copyright (c) Microsoft. All rights reserved.


from unittest.mock import patch

import pytest
from azure.cosmos.aio import CosmosClient

from semantic_kernel.connectors.azure_cosmos_db import CosmosNoSqlCollection, CosmosNoSqlStore
from semantic_kernel.exceptions import VectorStoreInitializationException


def test_azure_cosmos_db_no_sql_store_init(
    clear_azure_cosmos_db_no_sql_env,
    database_name: str,
    url: str,
    key: str,
) -> None:
    """Test the initialization of an AzureCosmosDBNoSQLStore object."""
    vector_store = CosmosNoSqlStore(url=url, key=key, database_name=database_name)

    assert vector_store is not None
    assert vector_store.database_name == database_name
    assert vector_store.cosmos_client is not None
    assert vector_store.create_database is False


def test_azure_cosmos_db_no_sql_store_init_env(azure_cosmos_db_no_sql_unit_test_env) -> None:
    """Test the initialization of an AzureCosmosDBNoSQLStore object with environment variables."""
    vector_store = CosmosNoSqlStore()

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
        CosmosNoSqlStore(env_file_path="fake_path")


@pytest.mark.parametrize("exclude_list", [["AZURE_COSMOS_DB_NO_SQL_DATABASE_NAME"]], indirect=True)
def test_azure_cosmos_db_no_sql_store_init_no_database_name(
    azure_cosmos_db_no_sql_unit_test_env,
) -> None:
    """Test the initialization of an AzureCosmosDBNoSQLStore object with missing database name."""
    with pytest.raises(
        VectorStoreInitializationException, match="The name of the Azure Cosmos DB NoSQL database is missing."
    ):
        CosmosNoSqlStore(env_file_path="fake_path")


def test_azure_cosmos_db_no_sql_store_invalid_settings(
    clear_azure_cosmos_db_no_sql_env,
) -> None:
    """Test the initialization of an AzureCosmosDBNoSQLStore object with invalid settings."""
    with pytest.raises(VectorStoreInitializationException, match="Failed to validate Azure Cosmos DB NoSQL settings."):
        CosmosNoSqlStore(url="invalid_url")


@patch.object(CosmosNoSqlCollection, "__init__", return_value=None)
def test_azure_cosmos_db_no_sql_store_get_collection(
    mock_azure_cosmos_db_no_sql_collection_init,
    azure_cosmos_db_no_sql_unit_test_env,
    collection_name: str,
    record_type,
) -> None:
    """Test the get_collection method of an AzureCosmosDBNoSQLStore object."""
    vector_store = CosmosNoSqlStore()

    collection = vector_store.get_collection(collection_name=collection_name, record_type=record_type)

    assert collection is not None
    mock_azure_cosmos_db_no_sql_collection_init.assert_called_once_with(
        record_type=record_type,
        definition=None,
        collection_name=collection_name,
        database_name=azure_cosmos_db_no_sql_unit_test_env["AZURE_COSMOS_DB_NO_SQL_DATABASE_NAME"],
        embedding_generator=None,
        url=azure_cosmos_db_no_sql_unit_test_env["AZURE_COSMOS_DB_NO_SQL_URL"],
        key=azure_cosmos_db_no_sql_unit_test_env["AZURE_COSMOS_DB_NO_SQL_KEY"],
        cosmos_client=vector_store.cosmos_client,
        partition_key=None,
        create_database=vector_store.create_database,
        env_file_path=None,
        env_file_encoding=None,
    )


@patch.object(CosmosClient, "close", return_value=None)
async def test_client_is_closed(mock_cosmos_client_close, azure_cosmos_db_no_sql_unit_test_env) -> None:
    """Test the close method of an AzureCosmosDBNoSQLStore object."""
    async with CosmosNoSqlStore() as vector_store:
        assert vector_store.cosmos_client is not None

    mock_cosmos_client_close.assert_called()
