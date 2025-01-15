# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import MagicMock, patch

import pytest
from pymongo import MongoClient

from semantic_kernel.connectors.memory.mongodb_atlas.mongodb_atlas_collection import MongoDBAtlasCollection


@pytest.fixture
def mock_mongo_client():
    with patch("pymongo.AsyncMongoClient") as mock:
        yield mock


@pytest.fixture
def mock_mongo_db(mock_mongo_client):
    mock_db = MagicMock()
    mock_mongo_client.return_value.get_database.return_value = mock_db
    yield mock_db


def test_mongodb_atlas_collection_initialization(mock_mongo_client):
    collection = MongoDBAtlasCollection(
        data_model_type=dict,
        collection_name="test_collection",
        mongo_client=mock_mongo_client,
    )
    assert collection.mongo_client is not None
    assert isinstance(collection.mongo_client, MongoClient)


def test_mongodb_atlas_collection_upsert(mock_mongo_db):
    collection = MongoDBAtlasCollection(
        data_model_type=dict,
        collection_name="test_collection",
        mongo_client=mock_mongo_db,
    )
    mock_mongo_db.get_collection.return_value.insert_one.return_value.inserted_id = "test_id"
    result = collection._inner_upsert([{"_id": "test_id", "data": "test_data"}])
    assert result == ["test_id"]


def test_mongodb_atlas_collection_get(mock_mongo_db):
    collection = MongoDBAtlasCollection(
        data_model_type=dict,
        collection_name="test_collection",
        mongo_client=mock_mongo_db,
    )
    mock_mongo_db.get_collection.return_value.find_one.return_value = {"_id": "test_id", "data": "test_data"}
    result = collection._inner_get(["test_id"])
    assert result == [{"_id": "test_id", "data": "test_data"}]


def test_mongodb_atlas_collection_delete(mock_mongo_db):
    collection = MongoDBAtlasCollection(
        data_model_type=dict,
        collection_name="test_collection",
        mongo_client=mock_mongo_db,
    )
    collection._inner_delete(["test_id"])
    mock_mongo_db.get_collection.return_value.delete_one.assert_called_with({"_id": "test_id"})
