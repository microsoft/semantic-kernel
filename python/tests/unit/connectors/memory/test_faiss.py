# Copyright (c) Microsoft. All rights reserved.

from typing import Annotated

import faiss
from pydantic import BaseModel
from pytest import approx, fixture, mark, raises

from semantic_kernel.connectors.faiss import FaissCollection, FaissStore
from semantic_kernel.data.vector import (
    DistanceFunction,
    VectorStoreCollectionDefinition,
    VectorStoreField,
    vectorstoremodel,
)
from semantic_kernel.exceptions import VectorStoreInitializationException, VectorStoreOperationException


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
async def test_ensure_collection_exists(store, data_model_def, dist):
    for field in data_model_def.fields:
        if field.name == "vector":
            field.distance_function = dist
    collection = store.get_collection(collection_name="test", record_type=dict, definition=data_model_def)
    await collection.ensure_collection_exists()
    assert collection.inner_storage == {}
    assert collection.indexes
    assert collection.indexes["vector"] is not None


async def test_ensure_collection_exists_incompatible_dist(store, data_model_def):
    for field in data_model_def.fields:
        if field.name == "vector":
            field.distance_function = "cosine_distance"
    collection = store.get_collection(collection_name="test", record_type=dict, definition=data_model_def)
    with raises(VectorStoreInitializationException):
        await collection.ensure_collection_exists()


async def test_ensure_collection_exists_custom(store, data_model_def):
    index = faiss.IndexFlat(5)
    collection = store.get_collection(collection_name="test", record_type=dict, definition=data_model_def)
    await collection.ensure_collection_exists(index=index)
    assert collection.inner_storage == {}
    assert collection.indexes
    assert collection.indexes["vector"] is not None
    assert collection.indexes["vector"] == index
    assert collection.indexes["vector"].is_trained is True
    await collection.ensure_collection_deleted()


async def test_ensure_collection_exists_custom_untrained(store, data_model_def):
    index = faiss.IndexIVFFlat(faiss.IndexFlat(5), 5, 10)
    collection = store.get_collection(collection_name="test", record_type=dict, definition=data_model_def)
    with raises(VectorStoreInitializationException):
        await collection.ensure_collection_exists(index=index)
    del index


async def test_ensure_collection_exists_custom_dict(store, data_model_def):
    index = faiss.IndexFlat(5)
    collection = store.get_collection(collection_name="test", record_type=dict, definition=data_model_def)
    await collection.ensure_collection_exists(indexes={"vector": index})
    assert collection.inner_storage == {}
    assert collection.indexes
    assert collection.indexes["vector"] is not None
    assert collection.indexes["vector"] == index
    await collection.ensure_collection_deleted()


@mark.parametrize("use_index_dict", [False, True], ids=["single-index", "index-dict"])
@mark.parametrize("index_kind", ["flat-l2", "flat-ip", "hnsw"])
async def test_custom_index_upsert_and_search(store, data_model_def, use_index_dict, index_kind):
    collection = store.get_collection(collection_name="test", record_type=dict, definition=data_model_def)
    records = [
        {"id": "first", "content": "first record", "vector": [1.0, 0.0, 0.0, 0.0, 0.0]},
        {"id": "second", "content": "second record", "vector": [-1.0, 0.0, 0.0, 0.0, 0.0]},
    ]

    for _ in range(2):
        if index_kind == "flat-l2":
            index = faiss.IndexFlatL2(5)
        elif index_kind == "flat-ip":
            index = faiss.IndexFlatIP(5)
        else:
            index = faiss.IndexHNSWFlat(5, 4)
        kwargs = {"indexes": {"vector": index}} if use_index_dict else {"index": index}
        await collection.ensure_collection_exists(**kwargs)
        assert collection.indexes["vector"] is index

        assert await collection.upsert(records[0]) == "first"
        key_map = collection.indexes_key_map["vector"]
        await collection.ensure_collection_exists(**kwargs)
        assert collection.indexes_key_map["vector"] is key_map
        assert key_map == {"first": 0}
        assert await collection.upsert(records[1:]) == ["second"]
        assert key_map == {"first": 0, "second": 1}

        results = await collection.search(
            vector=records[0]["vector"], top=2, include_total_count=True, include_vectors=True
        )
        assert results.total_count == 2
        assert [result.record async for result in results.results] == records
        assert await collection.get("first", include_vectors=True) == records[0]
        assert index.ntotal == 2

        await collection.ensure_collection_deleted()
        assert collection.indexes == {}
        assert collection.indexes_key_map == {}
        assert collection.inner_storage == {}


@fixture(scope="function")
def aliased_definition(data_model_def) -> VectorStoreCollectionDefinition:
    """Only the key field declares a storage_name.

    This mirrors the InMemory test for the same behaviour and keeps the data and
    vector fields on their logical names, so the record reaches _inner_upsert
    under whichever serialization the record type produces.
    """
    data_model_def.key_field.storage_name = "stored_id"
    return data_model_def


@vectorstoremodel
class AliasedModel(BaseModel):
    id: Annotated[str, VectorStoreField("key", storage_name="stored_id")]
    content: Annotated[str, VectorStoreField("data")] = "test content"
    vector: Annotated[
        list[float] | None,
        VectorStoreField(
            "vector",
            dimensions=5,
            index_kind="flat",
            distance_function="dot_prod",
            type="float",
        ),
    ] = None


@mark.parametrize("model_kind", ["dict", "pydantic"], ids=["dict", "pydantic"])
async def test_upsert_with_key_storage_name(aliased_definition, model_kind):
    """A key field with a storage_name must upsert whichever shape it serializes to."""
    model_type = {"dict": dict, "pydantic": AliasedModel}[model_kind]
    collection = FaissCollection(record_type=model_type, definition=aliased_definition, collection_name="test-alias")
    record = model_type(id="testid", content="test content", vector=[1.0, 0.0, 0.0, 0.0, 0.0])
    await collection.ensure_collection_exists()

    assert await collection.upsert(record) == "testid"
    assert collection.indexes_key_map["vector"] == {"testid": 0}
    assert set(collection.inner_storage) == {"testid"}

    results = await collection.search(vector=[1.0, 0.0, 0.0, 0.0, 0.0], top=1, include_vectors=True)
    assert [result.record async for result in results.results] == [record]
    await collection.ensure_collection_deleted()


@vectorstoremodel
class VectorAliasedModel(BaseModel):
    id: Annotated[str, VectorStoreField("key", type="str")]
    content: Annotated[str, VectorStoreField("data", type="str")] = "test content"
    embedding: Annotated[
        list[float] | None,
        VectorStoreField(
            "vector",
            storage_name="vec",
            dimensions=5,
            index_kind="flat",
            distance_function="dot_prod",
            type="float",
        ),
    ] = None


def vector_aliased_definition() -> VectorStoreCollectionDefinition:
    return VectorStoreCollectionDefinition(
        fields=[
            VectorStoreField("key", name="id", type="str"),
            VectorStoreField("data", name="content", type="str"),
            VectorStoreField(
                "vector",
                name="embedding",
                storage_name="vec",
                dimensions=5,
                index_kind="flat",
                distance_function="dot_prod",
                type="float",
            ),
        ]
    )


async def test_upsert_with_vector_storage_name_pydantic_model():
    """A pydantic model_dump keeps the logical vector name; the vector must still resolve."""
    collection = FaissCollection(
        record_type=VectorAliasedModel, definition=vector_aliased_definition(), collection_name="test-vec-alias"
    )
    record = VectorAliasedModel(id="testid", embedding=[1.0, 0.0, 0.0, 0.0, 0.0])
    await collection.ensure_collection_exists()

    assert await collection.upsert(record) == "testid"
    assert collection.indexes["embedding"].ntotal == 1
    # Assert the indexed vector itself, so a wrong-but-valid vector cannot pass.
    assert collection.indexes["embedding"].reconstruct(0) == approx([1.0, 0.0, 0.0, 0.0, 0.0])

    results = await collection.search(vector=[1.0, 0.0, 0.0, 0.0, 0.0], top=1, include_vectors=True)
    assert [result.record async for result in results.results] == [record]
    await collection.ensure_collection_deleted()


async def test_upsert_with_custom_to_dict_logical_names(aliased_definition):
    """A custom to_dict that emits the logical key name must still resolve."""
    aliased_definition.to_dict = lambda record, **kwargs: {
        "id": record["id"],
        "content": record["content"],
        "vector": record["vector"],
    }
    collection = FaissCollection(record_type=dict, definition=aliased_definition, collection_name="test-alias-logical")
    record = {"id": "testid", "content": "test content", "vector": [1.0, 0.0, 0.0, 0.0, 0.0]}
    await collection.ensure_collection_exists()

    assert await collection.upsert(record) == "testid"
    assert collection.indexes_key_map["vector"] == {"testid": 0}
    await collection.ensure_collection_deleted()


async def test_upsert(faiss_collection):
    await faiss_collection.ensure_collection_exists()
    record = {"id": "testid", "content": "test content", "vector": [0.1, 0.2, 0.3, 0.4, 0.5]}
    key = await faiss_collection.upsert(record)
    assert key == "testid"
    assert faiss_collection.inner_storage == {"testid": record}
    await faiss_collection.ensure_collection_deleted()


async def test_search_on_empty_collection_returns_no_results(faiss_collection):
    """An empty index has nothing to search; faiss would otherwise assert k > 0."""
    await faiss_collection.ensure_collection_exists()

    results = await faiss_collection.search(vector=[0.1, 0.2, 0.3, 0.4, 0.5], top=3, include_total_count=True)
    assert [result async for result in results.results] == []
    assert results.total_count == 0
    await faiss_collection.ensure_collection_deleted()


async def test_search_on_empty_collection_still_validates_the_filter(faiss_collection):
    """An empty index returns early, but an invalid filter must still raise."""
    await faiss_collection.ensure_collection_exists()

    with raises(VectorStoreOperationException):
        await faiss_collection.search(vector=[0.1, 0.2, 0.3, 0.4, 0.5], top=3, filter="not valid (")
    await faiss_collection.ensure_collection_deleted()


async def test_search_after_deleting_every_record_returns_no_results(faiss_collection):
    """Deleting the last record empties the index; a later search must not raise."""
    await faiss_collection.ensure_collection_exists()
    record = {"id": "testid", "content": "test content", "vector": [0.1, 0.2, 0.3, 0.4, 0.5]}
    await faiss_collection.upsert(record)
    await faiss_collection.delete("testid")

    results = await faiss_collection.search(vector=record["vector"], top=3)
    assert [result async for result in results.results] == []
    await faiss_collection.ensure_collection_deleted()


async def test_get(faiss_collection):
    await faiss_collection.ensure_collection_exists()
    record = {"id": "testid", "content": "test content", "vector": [0.1, 0.2, 0.3, 0.4, 0.5]}
    await faiss_collection.upsert(record)
    result = await faiss_collection.get("testid")
    assert result["id"] == record["id"]
    assert result["content"] == record["content"]
    await faiss_collection.ensure_collection_deleted()


async def test_get_missing(faiss_collection):
    await faiss_collection.ensure_collection_exists()
    result = await faiss_collection.get("testid")
    assert result is None
    await faiss_collection.ensure_collection_deleted()


async def test_delete(faiss_collection):
    await faiss_collection.ensure_collection_exists()
    record = {"id": "testid", "content": "test content", "vector": [0.1, 0.2, 0.3, 0.4, 0.5]}
    await faiss_collection.upsert(record)
    await faiss_collection.delete("testid")
    assert faiss_collection.inner_storage == {}
    await faiss_collection.ensure_collection_deleted()


async def test_collection_exists(faiss_collection):
    assert await faiss_collection.collection_exists() is False
    await faiss_collection.ensure_collection_exists()
    assert await faiss_collection.collection_exists() is True
    await faiss_collection.ensure_collection_deleted()


async def test_ensure_collection_deleted(faiss_collection):
    await faiss_collection.ensure_collection_exists()
    record = {"id": "testid", "content": "test content", "vector": [0.1, 0.2, 0.3, 0.4, 0.5]}
    await faiss_collection.upsert(record)
    assert faiss_collection.inner_storage == {"testid": record}
    await faiss_collection.ensure_collection_deleted()
    assert faiss_collection.inner_storage == {}


@mark.parametrize("dist", [DistanceFunction.EUCLIDEAN_SQUARED_DISTANCE, DistanceFunction.DOT_PROD])
async def test_ensure_collection_exists_and_search(faiss_collection, dist):
    for field in faiss_collection.definition.fields:
        if field.name == "vector":
            field.distance_function = dist
    await faiss_collection.ensure_collection_exists()
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
