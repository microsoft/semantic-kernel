# Copyright (c) Microsoft. All rights reserved.


from unittest.mock import AsyncMock, patch

from pymongo import AsyncMongoClient
from pymongo.asynchronous.cursor import AsyncCursor
from pymongo.results import UpdateResult

from semantic_kernel.connectors.memory.mongodb_atlas.mongodb_atlas_collection import MongoDBAtlasCollection


def test_mongodb_atlas_collection_initialization(mongodb_atlas_unit_test_env, data_model_definition, mock_mongo_client):
    collection = MongoDBAtlasCollection(
        data_model_type=dict,
        data_model_definition=data_model_definition,
        collection_name="test_collection",
        mongo_client=mock_mongo_client,
    )
    assert collection.mongo_client is not None
    assert isinstance(collection.mongo_client, AsyncMongoClient)


async def test_mongodb_atlas_collection_upsert(mongodb_atlas_unit_test_env, data_model_definition, mock_get_collection):
    collection = MongoDBAtlasCollection(
        data_model_type=dict,
        data_model_definition=data_model_definition,
        collection_name="test_collection",
    )
    with patch.object(collection, "_get_collection", new=mock_get_collection) as mock_get:
        result_mock = AsyncMock(spec=UpdateResult)
        result_mock.upserted_id = ["test_id"]
        mock_get.return_value.update_many.return_value = result_mock
        result = await collection._inner_upsert([{"_id": "test_id", "data": "test_data"}])
        assert result == ["test_id"]


async def test_mongodb_atlas_collection_get(mongodb_atlas_unit_test_env, data_model_definition, mock_get_collection):
    collection = MongoDBAtlasCollection(
        data_model_type=dict,
        data_model_definition=data_model_definition,
        collection_name="test_collection",
    )
    with patch.object(collection, "_get_collection", new=mock_get_collection) as mock_get:
        result_mock = AsyncMock(spec=AsyncCursor)
        result_mock.to_list.return_value = [{"_id": "test_id", "data": "test_data"}]
        mock_get.return_value.find.return_value = result_mock
        result = await collection._inner_get(["test_id"])
        assert result == [{"_id": "test_id", "data": "test_data"}]


async def test_mongodb_atlas_collection_delete(mongodb_atlas_unit_test_env, data_model_definition, mock_get_collection):
    collection = MongoDBAtlasCollection(
        data_model_type=dict,
        data_model_definition=data_model_definition,
        collection_name="test_collection",
    )
    with patch.object(collection, "_get_collection", new=mock_get_collection) as mock_get:
        await collection._inner_delete(["test_id"])
        mock_get.return_value.delete_many.assert_called_with({"_id": {"$in": ["test_id"]}})
