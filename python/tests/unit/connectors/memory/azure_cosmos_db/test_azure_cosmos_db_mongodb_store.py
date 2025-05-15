# Copyright (c) Microsoft. All rights reserved.

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel, Field, ValidationError
from pymongo import AsyncMongoClient

import semantic_kernel.connectors.memory.azure_cosmos_db.azure_cosmos_db_mongodb_store as store_module
from semantic_kernel.connectors.memory.azure_cosmos_db.azure_cosmos_db_mongodb_store import (
    AzureCosmosDBforMongoDBStore,
)
from semantic_kernel.exceptions import VectorStoreInitializationException


def test_init_with_provided_mongo_client_sets_attributes() -> None:
    """Test that providing a mongo_client bypasses settings and sets attributes correctly."""
    # Arrange: create a dummy mongo client and cast to correct type for type checker
    mock_client = AsyncMock(spec=AsyncMongoClient)
    # Act: instantiate the store with the dummy client and custom database name
    store = AzureCosmosDBforMongoDBStore(mongo_client=mock_client, database_name="custom_db")
    # Assert: the store should use the provided client and database name
    assert store.mongo_client is mock_client
    assert store.database_name == "custom_db"
    # managed_client should be False since client was provided
    assert store.managed_client is False


def test_init_with_settings_successful(monkeypatch) -> None:
    """Test that when no mongo_client is provided, settings are loaded and AsyncMongoClient is created."""

    # Arrange: dummy settings that provide connection_string and database_name
    class DummySettings:
        def __init__(self, *args, **kwargs):
            # Simulate SecretStr-like object with get_secret_value
            self.connection_string = SimpleNamespace(get_secret_value=lambda: "fake_conn_str")
            self.database_name = "settings_db"

    # Monkey-patch the settings class in the module
    monkeypatch.setattr(
        "semantic_kernel.connectors.memory.azure_cosmos_db.azure_cosmos_db_mongodb_settings.AzureCosmosDBforMongoDBSettings",
        DummySettings,
    )

    # Dummy AsyncMongoClient to capture init args
    init_args = {}

    class DummyClient(AsyncMongoClient):
        def __init__(self, conn_str, driver=None):
            init_args["conn_str"] = conn_str
            init_args["driver"] = driver

    monkeypatch.setattr(
        store_module,
        "AsyncMongoClient",
        DummyClient,
    )
    # Act: instantiate without mongo_client
    store = AzureCosmosDBforMongoDBStore(connection_string=None, env_file_path=".env", env_file_encoding="utf-8")
    # Assert: AsyncMongoClient was called with secret value and driver info
    assert init_args.get("conn_str") == "fake_conn_str"
    assert hasattr(init_args.get("driver"), "name")
    # The store should use DummyClient and settings.database_name
    assert isinstance(store.mongo_client, DummyClient)
    assert store.database_name == "settings_db"
    # managed_client should be True when client is created internally
    assert store.managed_client is True


def test_init_settings_validation_error_raises(monkeypatch) -> None:
    """Test that ValidationError during settings initialization is wrapped in VectorStoreInitializationException."""

    class FakeModel(BaseModel):
        connection_string: str = Field(...)

    try:
        FakeModel()
    except ValidationError as e:
        fake_error = e

    class DummySettingsError:
        def __init__(self, *args, **kwargs):
            raise fake_error

    monkeypatch.setattr(
        "semantic_kernel.connectors.memory.azure_cosmos_db.azure_cosmos_db_mongodb_settings.AzureCosmosDBforMongoDBSettings",
        DummySettingsError,
    )

    with pytest.raises(VectorStoreInitializationException) as excinfo:
        AzureCosmosDBforMongoDBStore(connection_string=None)
    assert "Failed to create MongoDB Atlas settings." in str(excinfo.value)


def test_init_missing_connection_string_raises(monkeypatch) -> None:
    """Test that missing connection_string after settings init raises exception."""

    # DummySettings that sets connection_string to None
    class DummySettingsNoConn:
        def __init__(self, *args, **kwargs):
            self.connection_string = None
            self.database_name = "db_after_no_conn"

    monkeypatch.setattr(
        "semantic_kernel.connectors.memory.azure_cosmos_db.azure_cosmos_db_mongodb_settings.AzureCosmosDBforMongoDBSettings",
        DummySettingsNoConn,
    )

    with pytest.raises(VectorStoreInitializationException) as excinfo:
        AzureCosmosDBforMongoDBStore()
    assert "The connection string is missing." in str(excinfo.value)
