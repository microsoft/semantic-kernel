# Copyright (c) Microsoft. All rights reserved.

import pytest


@pytest.fixture()
def database_name():
    """Fixture for the database name."""
    return "test_database"


@pytest.fixture()
def collection_name():
    """Fixture for the collection name."""
    return "test_collection"


@pytest.fixture()
def url():
    """Fixture for the url."""
    return "https://test.cosmos.azure.com/"


@pytest.fixture()
def key():
    """Fixture for the key."""
    return "test_key"


@pytest.fixture()
def azure_cosmos_db_mongo_db_unit_test_env(monkeypatch, url, key, database_name, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for Azure Cosmos DB NoSQL unit tests."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {
        "AZURE_COSMOS_DB_MONGODB_CONNECTION_STRING": url,
        "AZURE_COSMOS_DB_MONGODB_DATABASE_NAME": database_name,
    }

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@pytest.fixture()
def azure_cosmos_db_no_sql_unit_test_env(monkeypatch, url, key, database_name, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for Azure Cosmos DB NoSQL unit tests."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {
        "AZURE_COSMOS_DB_NO_SQL_URL": url,
        "AZURE_COSMOS_DB_NO_SQL_KEY": key,
        "AZURE_COSMOS_DB_NO_SQL_DATABASE_NAME": database_name,
    }

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@pytest.fixture()
def clear_azure_cosmos_db_no_sql_env(monkeypatch):
    """Fixture to clear the environment variables for Weaviate unit tests."""
    monkeypatch.delenv("AZURE_COSMOS_DB_NO_SQL_URL", raising=False)
    monkeypatch.delenv("AZURE_COSMOS_DB_NO_SQL_KEY", raising=False)
    monkeypatch.delenv("AZURE_COSMOS_DB_NO_SQL_DATABASE_NAME", raising=False)
