# Copyright (c) Microsoft. All rights reserved.

import faiss
from pytest import fixture, mark, raises

from semantic_kernel.connectors.faiss import FaissCollection, FaissStore
from semantic_kernel.data.vector import DistanceFunction, VectorStoreCollectionDefinition, VectorStoreField
from semantic_kernel.exceptions import VectorStoreInitializationException


@fixture(scope="function")
def data_model_def() -> VectorStoreCollectionDefinition:
    return VectorStoreCollectionDefinition(
        fields=[
            VectorStoreField("key", name="id"),
            VectorStoreField("data", name="content"),
            VectorStoreField(
                "vector",
                name="vector",
                dimensions=5,
                index_kind="flat",
                distance_function="dot_prod",
                type="float",
            ),
        ]
    )


@fixture(scope="function")
def store() -> FaissStore:
    return FaissStore()


@fixture(scope="function")
def faiss_collection(data_model_def):
    return FaissCollection(record_type=dict, definition=data_model_def, collection_name="test")


async def test_store_get_collection(store, data_model_def):
    collection = store.get_collection(dict, definition=data_model_def, collection_name="test")
    assert collection.collection_name == "test"
    assert collection.record_type is dict
    assert collection.definition == data_model_def
    assert collection.inner_storage == {}


@mark.parametrize(
    "dist",
    [
        DistanceFunction.EUCLIDEAN_SQUARED_DISTANCE,
        DistanceFunction.DOT_PROD,
    ],
)
async def test_create_collection(store, data_model_def, dist):
    for field in data_model_def.fields:
        if field.name == "vector":
            field.distance_function = dist
    collection = store.get_collection(collection_name="test", record_type=dict, definition=data_model_def)
    await collection.create_collection()
    assert collection.inner_storage == {}
    assert collection.indexes
    assert collection.indexes["vector"] is not None


async def test_create_collection_incompatible_dist(store, data_model_def):
    for field in data_model_def.fields:
        if field.name == "vector":
            field.distance_function = "cosine_distance"
    collection = store.get_collection(collection_name="test", record_type=dict, definition=data_model_def)
    with raises(VectorStoreInitializationException):
        await collection.create_collection()


async def test_create_collection_custom(store, data_model_def):
    index = faiss.IndexFlat(5)
    collection = store.get_collection(collection_name="test", record_type=dict, definition=data_model_def)
    await collection.create_collection(index=index)
    assert collection.inner_storage == {}
    assert collection.indexes
    assert collection.indexes["vector"] is not None
    assert collection.indexes["vector"] == index
    assert collection.indexes["vector"].is_trained is True
    await collection.ensure_collection_deleted()


async def test_create_collection_custom_untrained(store, data_model_def):
    index = faiss.IndexIVFFlat(faiss.IndexFlat(5), 5, 10)
    collection = store.get_collection(collection_name="test", record_type=dict, definition=data_model_def)
    with raises(VectorStoreInitializationException):
        await collection.create_collection(index=index)
    del index


async def test_create_collection_custom_dict(store, data_model_def):
    index = faiss.IndexFlat(5)
    collection = store.get_collection(collection_name="test", record_type=dict, definition=data_model_def)
    await collection.create_collection(indexes={"vector": index})
    assert collection.inner_storage == {}
    assert collection.indexes
    assert collection.indexes["vector"] is not None
    assert collection.indexes["vector"] == index
    await collection.ensure_collection_deleted()


async def test_upsert(faiss_collection):
    await faiss_collection.create_collection()
    record = {"id": "testid", "content": "test content", "vector": [0.1, 0.2, 0.3, 0.4, 0.5]}
    key = await faiss_collection.upsert(record)
    assert key == "testid"
    assert faiss_collection.inner_storage == {"testid": record}
    await faiss_collection.ensure_collection_deleted()


async def test_get(faiss_collection):
    await faiss_collection.create_collection()
    record = {"id": "testid", "content": "test content", "vector": [0.1, 0.2, 0.3, 0.4, 0.5]}
    await faiss_collection.upsert(record)
    result = await faiss_collection.get("testid")
    assert result["id"] == record["id"]
    assert result["content"] == record["content"]
    await faiss_collection.ensure_collection_deleted()


async def test_get_missing(faiss_collection):
    await faiss_collection.create_collection()
    result = await faiss_collection.get("testid")
    assert result is None
    await faiss_collection.ensure_collection_deleted()


async def test_delete(faiss_collection):
    await faiss_collection.create_collection()
    record = {"id": "testid", "content": "test content", "vector": [0.1, 0.2, 0.3, 0.4, 0.5]}
    await faiss_collection.upsert(record)
    await faiss_collection.delete("testid")
    assert faiss_collection.inner_storage == {}
    await faiss_collection.ensure_collection_deleted()


async def test_does_collection_exist(faiss_collection):
    assert await faiss_collection.does_collection_exist() is False
    await faiss_collection.create_collection()
    assert await faiss_collection.does_collection_exist() is True
    await faiss_collection.ensure_collection_deleted()


async def test_delete_collection(faiss_collection):
    await faiss_collection.create_collection()
    record = {"id": "testid", "content": "test content", "vector": [0.1, 0.2, 0.3, 0.4, 0.5]}
    await faiss_collection.upsert(record)
    assert faiss_collection.inner_storage == {"testid": record}
    await faiss_collection.ensure_collection_deleted()
    assert faiss_collection.inner_storage == {}


@mark.parametrize("dist", [DistanceFunction.EUCLIDEAN_SQUARED_DISTANCE, DistanceFunction.DOT_PROD])
async def test_create_collection_and_search(faiss_collection, dist):
    for field in faiss_collection.definition.fields:
        if field.name == "vector":
            field.distance_function = dist
    await faiss_collection.create_collection()
    record1 = {"id": "testid1", "content": "test content", "vector": [1.0, 1.0, 1.0, 1.0, 1.0]}
    record2 = {"id": "testid2", "content": "test content", "vector": [-1.0, -1.0, -1.0, -1.0, -1.0]}
    await faiss_collection.upsert([record1, record2])
    results = await faiss_collection.search(
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
    await faiss_collection.ensure_collection_deleted()
