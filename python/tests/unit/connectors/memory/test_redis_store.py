# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch

import numpy as np
from pytest import fixture, mark, raises
from redis.asyncio.client import Redis

from semantic_kernel.connectors.memory.redis.const import RedisCollectionTypes
from semantic_kernel.connectors.memory.redis.redis_collection import RedisHashsetCollection, RedisJsonCollection
from semantic_kernel.connectors.memory.redis.redis_store import RedisStore
from semantic_kernel.exceptions.memory_connector_exceptions import (
    MemoryConnectorException,
    MemoryConnectorInitializationError,
)

BASE_PATH = "redis.asyncio.client.Redis"
BASE_PATH_FT = "redis.commands.search.AsyncSearch"
BASE_PATH_JSON = "redis.commands.json.commands.JSONCommands"


@fixture
def vector_store(redis_unit_test_env):
    return RedisStore(env_file_path="test.env")


@fixture
def collection_hash(redis_unit_test_env, data_model_definition):
    return RedisHashsetCollection(
        data_model_type=dict,
        collection_name="test",
        data_model_definition=data_model_definition,
        env_file_path="test.env",
    )


@fixture
def collection_json(redis_unit_test_env, data_model_definition):
    return RedisJsonCollection(
        data_model_type=dict,
        collection_name="test",
        data_model_definition=data_model_definition,
        env_file_path="test.env",
    )


@fixture
def collection_with_prefix_hash(redis_unit_test_env, data_model_definition):
    return RedisHashsetCollection(
        data_model_type=dict,
        collection_name="test",
        data_model_definition=data_model_definition,
        prefix_collection_name_to_key_names=True,
        env_file_path="test.env",
    )


@fixture
def collection_with_prefix_json(redis_unit_test_env, data_model_definition):
    return RedisJsonCollection(
        data_model_type=dict,
        collection_name="test",
        data_model_definition=data_model_definition,
        prefix_collection_name_to_key_names=True,
        env_file_path="test.env",
    )


@fixture(autouse=True)
def moc_list_collection_names():
    with patch(f"{BASE_PATH}.execute_command") as mock_get_collections:
        mock_get_collections.return_value = [b"test"]
        yield mock_get_collections


@fixture(autouse=True)
def mock_does_collection_exist():
    with patch(f"{BASE_PATH_FT}.info", new=AsyncMock()) as mock_collection_exists:
        mock_collection_exists.return_value = True
        yield mock_collection_exists


@fixture(autouse=True)
def mock_create_collection():
    with patch(f"{BASE_PATH_FT}.create_index", new=AsyncMock()) as mock_recreate_collection:
        yield mock_recreate_collection


@fixture(autouse=True)
def mock_delete_collection():
    with patch(f"{BASE_PATH_FT}.dropindex", new=AsyncMock()) as mock_delete_collection:
        yield mock_delete_collection


@fixture(autouse=True)
def mock_upsert_hash():
    with patch(f"{BASE_PATH}.hset", new=AsyncMock()) as mock_upsert:
        yield mock_upsert


@fixture(autouse=True)
def mock_upsert_json():
    with patch(f"{BASE_PATH_JSON}.set", new=AsyncMock()) as mock_upsert:
        yield mock_upsert


@fixture(autouse=True)
def mock_get_hash():
    with patch(f"{BASE_PATH}.hgetall", new=AsyncMock()) as mock_get:
        mock_get.return_value = {
            b"metadata": b'{"content": "content"}',
            b"vector": np.array([1.0, 2.0, 3.0]).tobytes(),
        }
        yield mock_get


@fixture(autouse=True)
def mock_get_json():
    with patch(f"{BASE_PATH_JSON}.mget", new=AsyncMock()) as mock_get:
        mock_get.return_value = [
            [
                {
                    "content": "content",
                    "vector": [1.0, 2.0, 3.0],
                }
            ]
        ]
        yield mock_get


@fixture(autouse=True)
def mock_delete_hash():
    with patch(f"{BASE_PATH}.delete", new=AsyncMock()) as mock_delete:
        yield mock_delete


@fixture(autouse=True)
def mock_delete_json():
    with patch(f"{BASE_PATH_JSON}.delete", new=AsyncMock()) as mock_delete:
        yield mock_delete


def test_vector_store_defaults(vector_store):
    assert vector_store.redis_database is not None
    assert vector_store.redis_database.connection_pool.connection_kwargs["host"] == "localhost"


def test_vector_store_with_client(redis_unit_test_env):
    vector_store = RedisStore(redis_database=Redis.from_url(redis_unit_test_env["REDIS_CONNECTION_STRING"]))
    assert vector_store.redis_database is not None
    assert vector_store.redis_database.connection_pool.connection_kwargs["host"] == "localhost"


@mark.parametrize("exclude_list", [["REDIS_CONNECTION_STRING"]], indirect=True)
def test_vector_store_fail(redis_unit_test_env):
    with raises(MemoryConnectorInitializationError, match="Failed to create Redis settings."):
        RedisStore(env_file_path="test.env")


@mark.asyncio
async def test_store_list_collection_names(vector_store, moc_list_collection_names):
    collections = await vector_store.list_collection_names()
    assert collections == ["test"]


@mark.parametrize("type_", ["hashset", "json"])
def test_get_collection(vector_store, data_model_definition, type_):
    if type_ == "hashset":
        collection = vector_store.get_collection(
            "test",
            data_model_type=dict,
            data_model_definition=data_model_definition,
            collection_type=RedisCollectionTypes.HASHSET,
        )
        assert isinstance(collection, RedisHashsetCollection)
    else:
        collection = vector_store.get_collection(
            "test",
            data_model_type=dict,
            data_model_definition=data_model_definition,
            collection_type=RedisCollectionTypes.JSON,
        )
        assert isinstance(collection, RedisJsonCollection)
    assert collection.collection_name == "test"
    assert collection.redis_database == vector_store.redis_database
    assert collection.data_model_type is dict
    assert collection.data_model_definition == data_model_definition
    assert vector_store.vector_record_collections["test"] == collection


@mark.parametrize("type_", ["hashset", "json"])
def test_collection_init(redis_unit_test_env, data_model_definition, type_):
    if type_ == "hashset":
        collection = RedisHashsetCollection(
            data_model_type=dict,
            collection_name="test",
            data_model_definition=data_model_definition,
            env_file_path="test.env",
        )
    else:
        collection = RedisJsonCollection(
            data_model_type=dict,
            collection_name="test",
            data_model_definition=data_model_definition,
            env_file_path="test.env",
        )
    assert collection.collection_name == "test"
    assert collection.redis_database is not None
    assert collection.data_model_type is dict
    assert collection.data_model_definition == data_model_definition
    assert collection.prefix_collection_name_to_key_names is False


@mark.parametrize("type_", ["hashset", "json"])
def test_init_with_type(redis_unit_test_env, data_model_type, type_):
    if type_ == "hashset":
        collection = RedisHashsetCollection(data_model_type=data_model_type, collection_name="test")
    else:
        collection = RedisJsonCollection(data_model_type=data_model_type, collection_name="test")
    assert collection is not None
    assert collection.data_model_type is data_model_type
    assert collection.collection_name == "test"


@mark.parametrize("exclude_list", [["REDIS_CONNECTION_STRING"]], indirect=True)
def test_collection_fail(redis_unit_test_env, data_model_definition):
    with raises(MemoryConnectorInitializationError, match="Failed to create Redis settings."):
        RedisHashsetCollection(
            data_model_type=dict,
            collection_name="test",
            data_model_definition=data_model_definition,
            env_file_path="test.env",
        )
    with raises(MemoryConnectorInitializationError, match="Failed to create Redis settings."):
        RedisJsonCollection(
            data_model_type=dict,
            collection_name="test",
            data_model_definition=data_model_definition,
            env_file_path="test.env",
        )


@mark.asyncio
@mark.parametrize("type_", ["hashset", "json"])
async def test_upsert(collection_hash, collection_json, type_):
    if type_ == "hashset":
        record = {
            "name": "id1",
            "mapping": {
                "metadata": {"content": "content"},
                "vector": [1.0, 2.0, 3.0],
            },
        }
    else:
        record = {
            "name": "id1",
            "value": {
                "content": "content",
                "vector": [1.0, 2.0, 3.0],
            },
        }
    collection = collection_hash if type_ == "hashset" else collection_json
    ids = await collection._inner_upsert([record])
    assert ids[0] == "id1"

    ids = await collection.upsert(record={"id": "id1", "content": "content", "vector": [1.0, 2.0, 3.0]})
    assert ids == "id1"


@mark.asyncio
async def test_upsert_with_prefix(collection_with_prefix_hash, collection_with_prefix_json):
    ids = await collection_with_prefix_hash.upsert(
        record={"id": "id1", "content": "content", "vector": [1.0, 2.0, 3.0]}
    )
    assert ids == "id1"
    ids = await collection_with_prefix_json.upsert(
        record={"id": "id1", "content": "content", "vector": [1.0, 2.0, 3.0]}
    )
    assert ids == "id1"


@mark.asyncio
@mark.parametrize("prefix", [True, False])
@mark.parametrize("type_", ["hashset", "json"])
async def test_get(
    collection_hash, collection_json, collection_with_prefix_hash, collection_with_prefix_json, type_, prefix
):
    if prefix:
        collection = collection_with_prefix_hash if type_ == "hashset" else collection_with_prefix_json
    else:
        collection = collection_hash if type_ == "hashset" else collection_json
    records = await collection._inner_get(["id1"])
    assert records is not None

    records = await collection.get("id1")
    assert records is not None


@mark.asyncio
@mark.parametrize("type_", ["hashset", "json"])
async def test_delete(collection_hash, collection_json, type_):
    collection = collection_hash if type_ == "hashset" else collection_json
    await collection._inner_delete(["id1"])


@mark.asyncio
async def test_does_collection_exist(collection_hash, mock_does_collection_exist):
    await collection_hash.does_collection_exist()


@mark.asyncio
async def test_does_collection_exist_false(collection_hash, mock_does_collection_exist):
    mock_does_collection_exist.side_effect = Exception
    exists = await collection_hash.does_collection_exist()
    assert not exists


@mark.asyncio
async def test_delete_collection(collection_hash, mock_delete_collection):
    await collection_hash.delete_collection()
    await collection_hash.delete_collection()


@mark.asyncio
async def test_create_index(collection_hash, mock_create_collection):
    await collection_hash.create_collection()


@mark.asyncio
async def test_create_index_manual(collection_hash, mock_create_collection):
    from redis.commands.search.indexDefinition import IndexDefinition, IndexType

    fields = ["fields"]
    index_definition = IndexDefinition(prefix="test:", index_type=IndexType.HASH)
    await collection_hash.create_collection(index_definition=index_definition, fields=fields)


@mark.asyncio
async def test_create_index_fail(collection_hash, mock_create_collection):
    with raises(MemoryConnectorException, match="Invalid index type supplied."):
        await collection_hash.create_collection(index_definition="index_definition", fields="fields")
