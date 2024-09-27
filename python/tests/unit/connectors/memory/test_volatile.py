# Copyright (c) Microsoft. All rights reserved.

from pytest import fixture, mark

from semantic_kernel.connectors.memory.volatile.volatile_collection import (
    VolatileCollection,
)
from semantic_kernel.connectors.memory.volatile.volatile_store import VolatileStore


@fixture
def collection(data_model_definition):
    return VolatileCollection("test", dict, data_model_definition)


def test_store_init():
    store = VolatileStore()
    assert store.vector_record_collections == {}


@mark.asyncio
async def test_store_get_collection(data_model_definition):
    store = VolatileStore()
    collection = store.get_collection("test", dict, data_model_definition)
    assert collection.collection_name == "test"
    assert collection.data_model_type is dict
    assert collection.data_model_definition == data_model_definition
    assert collection.inner_storage == {}
    assert (await store.list_collection_names()) == ["test"]


@mark.asyncio
async def test_upsert(collection):
    record = {
        "id": "testid",
        "content": "test content",
        "vector": [0.1, 0.2, 0.3, 0.4, 0.5],
    }
    key = await collection.upsert(record)
    assert key == "testid"
    assert collection.inner_storage == {"testid": record}


@mark.asyncio
async def test_get(collection):
    record = {
        "id": "testid",
        "content": "test content",
        "vector": [0.1, 0.2, 0.3, 0.4, 0.5],
    }
    await collection.upsert(record)
    result = await collection.get("testid")
    assert result == record


@mark.asyncio
async def test_get_missing(collection):
    result = await collection.get("testid")
    assert result is None


@mark.asyncio
async def test_delete(collection):
    record = {
        "id": "testid",
        "content": "test content",
        "vector": [0.1, 0.2, 0.3, 0.4, 0.5],
    }
    await collection.upsert(record)
    await collection.delete("testid")
    assert collection.inner_storage == {}


@mark.asyncio
async def test_does_collection_exist(collection):
    assert await collection.does_collection_exist() is True


@mark.asyncio
async def test_delete_collection(collection):
    record = {
        "id": "testid",
        "content": "test content",
        "vector": [0.1, 0.2, 0.3, 0.4, 0.5],
    }
    await collection.upsert(record)
    assert collection.inner_storage == {"testid": record}
    await collection.delete_collection()
    assert collection.inner_storage == {}


@mark.asyncio
async def test_create_collection(collection):
    await collection.create_collection()
