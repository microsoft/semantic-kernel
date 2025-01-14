# Copyright (c) Microsoft. All rights reserved.

import pytest
from unittest.mock import MagicMock, patch
from pymongo import MongoClient
from semantic_kernel.connectors.memory.mongodb_atlas.mongodb_atlas_store import MongoDBAtlasStore
from semantic_kernel.connectors.memory.mongodb_atlas.mongodb_atlas_collection import MongoDBAtlasCollection
from semantic_kernel.data.record_definition import VectorStoreRecordDefinition


@pytest.fixture
def mock_mongo_client():
    with patch("pymongo.MongoClient") as mock:
        yield mock


@pytest.fixture
def mock_mongo_db(mock_mongo_client):
    mock_db = MagicMock()
    mock_mongo_client.return_value.get_database.return_value = mock_db
    yield mock_db


def test_mongodb_atlas_store_initialization(mock_mongo_client):
    store = MongoDBAtlasStore(connection_string="mongodb://test", database_name="test_db")
    assert store.mongo_client is not None
    assert isinstance(store.mongo_client, MongoClient)


def test_mongodb_atlas_store_get_collection(mock_mongo_client):
    store = MongoDBAtlasStore(connection_string="mongodb://test", database_name="test_db")
    collection = store.get_collection(
        collection_name="test_collection",
        data_model_type=dict,
        data_model_definition=VectorStoreRecordDefinition(),
    )
    assert collection is not None
    assert isinstance(collection, MongoDBAtlasCollection)


def test_mongodb_atlas_store_list_collection_names(mock_mongo_db):
    store = MongoDBAtlasStore(connection_string="mongodb://test", database_name="test_db")
    mock_mongo_db.list_collection_names.return_value = ["test_collection"]
    result = store.list_collection_names()
    assert result == ["test_collection"]
