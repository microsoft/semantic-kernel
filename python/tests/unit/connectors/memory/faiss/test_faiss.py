# Copyright (c) Microsoft. All rights reserved.

import faiss
from pytest import fixture, mark, raises

from semantic_kernel.connectors.memory.faiss import FaissCollection, FaissStore
from semantic_kernel.data import (
    VectorStoreRecordDataField,
    VectorStoreRecordDefinition,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.data.const import DistanceFunction
from semantic_kernel.data.vector_search import VectorSearchFilter, VectorSearchOptions
from semantic_kernel.exceptions import VectorStoreInitializationException


@fixture(scope="function")
def data_model_def() -> VectorStoreRecordDefinition:
    return VectorStoreRecordDefinition(
        fields={
            "id": VectorStoreRecordKeyField(),
            "content": VectorStoreRecordDataField(
                has_embedding=True,
                embedding_property_name="vector",
            ),
            "vector": VectorStoreRecordVectorField(
                dimensions=5,
                index_kind="flat",
                distance_function="dot_prod",
                property_type="float",
            ),
        }
    )


@fixture(scope="function")
def faiss_collection(data_model_def):
    return FaissCollection("test", dict, data_model_def)


def test_store_init():
    store = FaissStore()
    assert store.vector_record_collections == {}


async def test_store_get_collection(data_model_def):
    store = FaissStore()
    collection = store.get_collection("test", dict, data_model_def)
    assert collection.collection_name == "test"
    assert collection.data_model_type is dict
    assert collection.data_model_definition == data_model_def
    assert collection.inner_storage == {}
    assert (await store.list_collection_names()) == ["test"]


@mark.parametrize(
    "dist",
    [
        DistanceFunction.EUCLIDEAN_SQUARED_DISTANCE,
        DistanceFunction.DOT_PROD,
    ],
)
async def test_create_collection(data_model_def, dist):
    store = FaissStore()
    data_model_def.fields["vector"].distance_function = dist
    collection = store.get_collection("test", dict, data_model_def)
    await collection.create_collection()
    assert collection.inner_storage == {}
    assert collection.indexes
    assert collection.indexes["vector"] is not None


async def test_create_collection_incompatible_dist(data_model_def):
    store = FaissStore()
    data_model_def.fields["vector"].distance_function = "cosine_distance"
    collection = store.get_collection("test", dict, data_model_def)
    with raises(VectorStoreInitializationException):
        await collection.create_collection()


async def test_create_collection_custom(data_model_def):
    index = faiss.IndexFlat(5)
    store = FaissStore()
    collection = store.get_collection("test", dict, data_model_def)
    await collection.create_collection(index=index)
    assert collection.inner_storage == {}
    assert collection.indexes
    assert collection.indexes["vector"] is not None
    assert collection.indexes["vector"] == index
    assert collection.indexes["vector"].is_trained is True
    await collection.delete_collection()


async def test_create_collection_custom_untrained(data_model_def):
    index = faiss.IndexIVFFlat(faiss.IndexFlat(5), 5, 10)
    store = FaissStore()
    collection = store.get_collection("test", dict, data_model_def)
    with raises(VectorStoreInitializationException):
        await collection.create_collection(index=index)
    del index


async def test_create_collection_custom_dict(data_model_def):
    index = faiss.IndexFlat(5)
    store = FaissStore()
    collection = store.get_collection("test", dict, data_model_def)
    await collection.create_collection(indexes={"vector": index})
    assert collection.inner_storage == {}
    assert collection.indexes
    assert collection.indexes["vector"] is not None
    assert collection.indexes["vector"] == index
    await collection.delete_collection()


async def test_upsert(faiss_collection):
    await faiss_collection.create_collection()
    record = {"id": "testid", "content": "test content", "vector": [0.1, 0.2, 0.3, 0.4, 0.5]}
    key = await faiss_collection.upsert(record)
    assert key == "testid"
    assert faiss_collection.inner_storage == {"testid": record}
    await faiss_collection.delete_collection()


async def test_get(faiss_collection):
    await faiss_collection.create_collection()
    record = {"id": "testid", "content": "test content", "vector": [0.1, 0.2, 0.3, 0.4, 0.5]}
    await faiss_collection.upsert(record)
    result = await faiss_collection.get("testid")
    assert result == record
    await faiss_collection.delete_collection()


async def test_get_missing(faiss_collection):
    await faiss_collection.create_collection()
    result = await faiss_collection.get("testid")
    assert result is None
    await faiss_collection.delete_collection()


async def test_delete(faiss_collection):
    await faiss_collection.create_collection()
    record = {"id": "testid", "content": "test content", "vector": [0.1, 0.2, 0.3, 0.4, 0.5]}
    await faiss_collection.upsert(record)
    await faiss_collection.delete("testid")
    assert faiss_collection.inner_storage == {}
    await faiss_collection.delete_collection()


async def test_does_collection_exist(faiss_collection):
    assert await faiss_collection.does_collection_exist() is False
    await faiss_collection.create_collection()
    assert await faiss_collection.does_collection_exist() is True
    await faiss_collection.delete_collection()


async def test_delete_collection(faiss_collection):
    await faiss_collection.create_collection()
    record = {"id": "testid", "content": "test content", "vector": [0.1, 0.2, 0.3, 0.4, 0.5]}
    await faiss_collection.upsert(record)
    assert faiss_collection.inner_storage == {"testid": record}
    await faiss_collection.delete_collection()
    assert faiss_collection.inner_storage == {}


async def test_text_search(faiss_collection):
    await faiss_collection.create_collection()
    record = {"id": "testid", "content": "test content", "vector": [0.1, 0.2, 0.3, 0.4, 0.5]}
    await faiss_collection.upsert(record)
    results = await faiss_collection.text_search(search_text="content")
    assert len([res async for res in results.results]) == 1
    await faiss_collection.delete_collection()


async def test_text_search_with_filter(faiss_collection):
    await faiss_collection.create_collection()
    record = {"id": "testid", "content": "test content", "vector": [0.1, 0.2, 0.3, 0.4, 0.5]}
    await faiss_collection.upsert(record)
    results = await faiss_collection.text_search(
        search_text="content",
        options=VectorSearchOptions(
            filter=VectorSearchFilter.any_tag_equal_to("vector", 0.1).equal_to("content", "content")
        ),
    )
    assert len([res async for res in results.results]) == 1
    await faiss_collection.delete_collection()


@mark.parametrize("dist", [DistanceFunction.EUCLIDEAN_SQUARED_DISTANCE, DistanceFunction.DOT_PROD])
async def test_create_collection_and_search(faiss_collection, dist):
    faiss_collection.data_model_definition.fields["vector"].distance_function = dist
    await faiss_collection.create_collection()
    record1 = {"id": "testid1", "content": "test content", "vector": [1.0, 1.0, 1.0, 1.0, 1.0]}
    record2 = {"id": "testid2", "content": "test content", "vector": [-1.0, -1.0, -1.0, -1.0, -1.0]}
    await faiss_collection.upsert_batch([record1, record2])
    results = await faiss_collection.vectorized_search(
        vector=[0.9, 0.9, 0.9, 0.9, 0.9],
        options=VectorSearchOptions(vector_field_name="vector", include_total_count=True, include_vectors=True),
    )
    assert results.total_count == 2
    idx = 0
    async for res in results.results:
        assert res.record == record1 if idx == 0 else record2
        idx += 1
    await faiss_collection.delete_collection()
