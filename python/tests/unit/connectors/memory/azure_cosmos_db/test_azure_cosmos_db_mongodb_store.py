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


# def test_get_collection_creates_and_caches(monkeypatch) -> None:
#     """Test that get_collection creates a collection instance and caches it for subsequent calls."""
#     # Arrange: dummy mongo_client and store, cast for type checking
#     mock_client = AsyncMock(spec=AsyncMongoClient)
#     store = AzureCosmosDBforMongoDBStore(mongo_client=mock_client, database_name="cache_db")
#     # Dummy collection class to capture constructor calls
#     created = []

#     class DummyCollection(AzureCosmosDBforMongoDBCollection):
#         def __init__(
#             self, data_model_type, data_model_definition, mongo_client, collection_name, database_name, **kwargs
#         ):
#             # Record init parameters
#             created.append({
#                 "data_model_type": data_model_type,
#                 "data_model_definition": data_model_definition,
#                 "mongo_client": mongo_client,
#                 "collection_name": collection_name,
#                 "database_name": database_name,
#                 "kwargs": kwargs,
#             })

#     # Monkey-patch collection class
#     monkeypatch.setattr(
#         store_module,
#         "AzureCosmosDBforMongoDBCollection",
#         DummyCollection,
#     )

#     # Act: first call creates a new collection
#     col1 = store.get_collection(
#         collection_name="col1",
#         data_model_type=str,
#         data_model_definition=None,
#         extra_param=42,
#     )
#     # Assert: collection was created with correct parameters
#     assert len(created) == 1
#     init_params = created[0]
#     assert init_params["data_model_type"] is str
#     assert init_params["data_model_definition"] is None
#     assert init_params["mongo_client"] is mock_client
#     assert init_params["collection_name"] == "col1"
#     assert init_params["database_name"] == "cache_db"
#     assert init_params["kwargs"] == {"extra_param": 42}
#     # The returned object should be the DummyCollection instance
#     assert isinstance(col1, DummyCollection)

#     # Act: second call with the same name should return cached instance
#     col2 = store.get_collection(collection_name="col1", data_model_type=str, data_model_definition=None)
#     # Assert: no new creation and same instance returned
#     assert len(created) == 1
#     assert col2 is col1

#     # Act: calling with a new collection name creates another instance
#     col3 = store.get_collection(collection_name="col2", data_model_type=int, data_model_definition=None)
#     assert len(created) == 2
#     params_col2 = created[1]
#     assert params_col2["collection_name"] == "col2"
#     assert params_col2["data_model_type"] is int
#     assert col3 is not col1
