# Copyright (c) Microsoft. All rights reserved.

from pytest import fixture


@fixture()
def mongodb_atlas_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for MongoDB Atlas Unit Tests."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {"MONGODB_ATLAS_CONNECTION_STRING": "mongodb://test", "MONGODB_ATLAS_DATABASE_NAME": "test-database"}

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@fixture
def postgres_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for Postgres connector."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {"POSTGRES_CONNECTION_STRING": "host=localhost port=5432 dbname=postgres user=testuser password=example"}

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@fixture
def qdrant_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for QdrantConnector."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {"QDRANT_LOCATION": "http://localhost:6333"}

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@fixture
def redis_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for Redis."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {"REDIS_CONNECTION_STRING": "redis://localhost:6379"}

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@fixture
def pinecone_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for Pinecone."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {"PINECONE_API_KEY": "test_key"}

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@fixture
def sql_server_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for SQL Server."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {
        "SQL_SERVER_CONNECTION_STRING": "Driver={ODBC Driver 18 for SQL Server};Server=localhost;Database=testdb;User Id=testuser;Password=example;"  # noqa: E501
    }

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars
