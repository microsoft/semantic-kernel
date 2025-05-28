# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch

from pymongo import AsyncMongoClient
from pymongo.asynchronous.cursor import AsyncCursor
from pymongo.results import UpdateResult
from pytest import mark, raises

from semantic_kernel.connectors.mongodb import DEFAULT_DB_NAME, DEFAULT_SEARCH_INDEX_NAME, MongoDBAtlasCollection
from semantic_kernel.exceptions.vector_store_exceptions import VectorStoreInitializationException


def test_mongodb_atlas_collection_initialization(mongodb_atlas_unit_test_env, definition, mock_mongo_client):
    collection = MongoDBAtlasCollection(
        record_type=dict,
        definition=definition,
        collection_name="test_collection",
        mongo_client=mock_mongo_client,
    )
    assert collection.mongo_client is not None
    assert isinstance(collection.mongo_client, AsyncMongoClient)


@mark.parametrize("exclude_list", [["MONGODB_ATLAS_CONNECTION_STRING"]], indirect=True)
def test_mongodb_atlas_collection_initialization_fail(mongodb_atlas_unit_test_env, definition):
    with raises(VectorStoreInitializationException):
        MongoDBAtlasCollection(
            collection_name="test_collection",
            record_type=dict,
            definition=definition,
        )


@mark.parametrize("exclude_list", [["MONGODB_ATLAS_DATABASE_NAME", "MONGODB_ATLAS_INDEX_NAME"]], indirect=True)
def test_mongodb_atlas_collection_initialization_defaults(mongodb_atlas_unit_test_env, definition):
    collection = MongoDBAtlasCollection(
        collection_name="test_collection",
        record_type=dict,
        definition=definition,
    )
    assert collection.database_name == DEFAULT_DB_NAME
    assert collection.index_name == DEFAULT_SEARCH_INDEX_NAME


async def test_mongodb_atlas_collection_upsert(mongodb_atlas_unit_test_env, definition, mock_get_collection):
    collection = MongoDBAtlasCollection(
        record_type=dict,
        definition=definition,
        collection_name="test_collection",
    )
    with patch.object(collection, "_get_collection", new=mock_get_collection) as mock_get:
        result_mock = AsyncMock(spec=UpdateResult)
        result_mock.upserted_ids = {0: "test_id"}
        mock_get.return_value.bulk_write.return_value = result_mock
        result = await collection._inner_upsert([{"_id": "test_id", "data": "test_data"}])
        assert result == ["test_id"]


async def test_mongodb_atlas_collection_get(mongodb_atlas_unit_test_env, definition, mock_get_collection):
    collection = MongoDBAtlasCollection(
        record_type=dict,
        definition=definition,
        collection_name="test_collection",
    )
    with patch.object(collection, "_get_collection", new=mock_get_collection) as mock_get:
        result_mock = AsyncMock(spec=AsyncCursor)
        result_mock.to_list.return_value = [{"_id": "test_id", "data": "test_data"}]
        mock_get.return_value.find.return_value = result_mock
        result = await collection._inner_get(["test_id"])
        assert result == [{"_id": "test_id", "data": "test_data"}]


async def test_mongodb_atlas_collection_delete(mongodb_atlas_unit_test_env, definition, mock_get_collection):
    collection = MongoDBAtlasCollection(
        record_type=dict,
        definition=definition,
        collection_name="test_collection",
    )
    with patch.object(collection, "_get_collection", new=mock_get_collection) as mock_get:
        await collection._inner_delete(["test_id"])
        mock_get.return_value.delete_many.assert_called_with({"_id": {"$in": ["test_id"]}})


async def test_mongodb_atlas_collection_collection_exists(mongodb_atlas_unit_test_env, definition, mock_get_database):
    collection = MongoDBAtlasCollection(
        record_type=dict,
        definition=definition,
        collection_name="test_collection",
    )
    with patch.object(collection, "_get_database", new=mock_get_database) as mock_get:
        mock_get.return_value.list_collection_names.return_value = ["test_collection"]
        assert await collection.does_collection_exist()
