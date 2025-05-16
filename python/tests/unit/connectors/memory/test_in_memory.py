# Copyright (c) Microsoft. All rights reserved.

from pytest import fixture, mark

from semantic_kernel.connectors.memory.in_memory import InMemoryCollection, InMemoryStore
from semantic_kernel.data.const import DistanceFunction


@fixture
def collection(data_model_definition):
    return InMemoryCollection(collection_name="test", data_model_type=dict, data_model_definition=data_model_definition)


def test_store_init():
    store = InMemoryStore()
    assert store is not None


def test_store_get_collection(data_model_definition):
    store = InMemoryStore()
    collection = store.get_collection(
        collection_name="test", data_model_type=dict, data_model_definition=data_model_definition
    )
    assert collection.collection_name == "test"
    assert collection.data_model_type is dict
    assert collection.data_model_definition == data_model_definition


async def test_upsert(collection):
    record = {"id": "testid", "content": "test content", "vector": [0.1, 0.2, 0.3, 0.4, 0.5]}
    key = await collection.upsert(record)
    assert key == "testid"
    assert collection.inner_storage == {"testid": record}


async def test_get(collection):
    record = {"id": "testid", "content": "test content", "vector": [0.1, 0.2, 0.3, 0.4, 0.5]}
    await collection.upsert(record)
    result = await collection.get("testid")
    assert result["id"] == record["id"]
    assert result["content"] == record["content"]


async def test_get_missing(collection):
    result = await collection.get("testid")
    assert result is None


async def test_delete(collection):
    record = {"id": "testid", "content": "test content", "vector": [0.1, 0.2, 0.3, 0.4, 0.5]}
    await collection.upsert(record)
    await collection.delete("testid")
    assert collection.inner_storage == {}


async def test_does_collection_exist(collection):
    assert await collection.does_collection_exist() is True


async def test_delete_collection(collection):
    record = {"id": "testid", "content": "test content", "vector": [0.1, 0.2, 0.3, 0.4, 0.5]}
    await collection.upsert(record)
    assert collection.inner_storage == {"testid": record}
    await collection.delete_collection()
    assert collection.inner_storage == {}


async def test_create_collection(collection):
    await collection.create_collection()


@mark.parametrize(
    "distance_function",
    [
        DistanceFunction.COSINE_DISTANCE,
        DistanceFunction.COSINE_SIMILARITY,
        DistanceFunction.EUCLIDEAN_DISTANCE,
        DistanceFunction.MANHATTAN,
        DistanceFunction.EUCLIDEAN_SQUARED_DISTANCE,
        DistanceFunction.DOT_PROD,
        DistanceFunction.HAMMING,
    ],
)
async def test_vectorized_search_similar(collection, distance_function):
    for field in collection.data_model_definition.fields:
        if field.name == "vector":
            field.distance_function = distance_function
    record1 = {"id": "testid1", "content": "test content", "vector": [1.0, 1.0, 1.0, 1.0, 1.0]}
    record2 = {"id": "testid2", "content": "test content", "vector": [-1.0, -1.0, -1.0, -1.0, -1.0]}
    await collection.upsert([record1, record2])
    results = await collection.search(
        vector=[0.9, 0.9, 0.9, 0.9, 0.9],
        vector_property_name="vector",
        include_total_count=True,
        include_vectors=True,
    )
    assert results.total_count == 2
    idx = 0
    async for res in results.results:
        assert res.record == record1 if idx == 0 else record2
        idx += 1
