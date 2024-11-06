# Copyright (c) Microsoft. All rights reserved.

from pytest import fixture, mark

from semantic_kernel.connectors.memory.in_memory.in_memory_collection import InMemoryVectorCollection
from semantic_kernel.connectors.memory.in_memory.in_memory_store import InMemoryVectorStore
from semantic_kernel.data.const import DistanceFunction
from semantic_kernel.data.vector_search.vector_search_options import VectorSearchOptions


@fixture
def collection(data_model_definition):
    return InMemoryVectorCollection("test", dict, data_model_definition)


def test_store_init():
    store = InMemoryVectorStore()
    assert store.vector_record_collections == {}


@mark.asyncio
async def test_store_get_collection(data_model_definition):
    store = InMemoryVectorStore()
    collection = store.get_collection("test", dict, data_model_definition)
    assert collection.collection_name == "test"
    assert collection.data_model_type is dict
    assert collection.data_model_definition == data_model_definition
    assert collection.inner_storage == {}
    assert (await store.list_collection_names()) == ["test"]


@mark.asyncio
async def test_upsert(collection):
    record = {"id": "testid", "content": "test content", "vector": [0.1, 0.2, 0.3, 0.4, 0.5]}
    key = await collection.upsert(record)
    assert key == "testid"
    assert collection.inner_storage == {"testid": record}


@mark.asyncio
async def test_get(collection):
    record = {"id": "testid", "content": "test content", "vector": [0.1, 0.2, 0.3, 0.4, 0.5]}
    await collection.upsert(record)
    result = await collection.get("testid")
    assert result == record


@mark.asyncio
async def test_get_missing(collection):
    result = await collection.get("testid")
    assert result is None


@mark.asyncio
async def test_delete(collection):
    record = {"id": "testid", "content": "test content", "vector": [0.1, 0.2, 0.3, 0.4, 0.5]}
    await collection.upsert(record)
    await collection.delete("testid")
    assert collection.inner_storage == {}


@mark.asyncio
async def test_does_collection_exist(collection):
    assert await collection.does_collection_exist() is True


@mark.asyncio
async def test_delete_collection(collection):
    record = {"id": "testid", "content": "test content", "vector": [0.1, 0.2, 0.3, 0.4, 0.5]}
    await collection.upsert(record)
    assert collection.inner_storage == {"testid": record}
    await collection.delete_collection()
    assert collection.inner_storage == {}


@mark.asyncio
async def test_create_collection(collection):
    await collection.create_collection()


@mark.asyncio
async def test_text_search(collection):
    record = {"id": "testid", "content": "test content", "vector": [0.1, 0.2, 0.3, 0.4, 0.5]}
    await collection.upsert(record)
    results = await collection.text_search(search_text="content")
    assert len([res async for res in results.results]) == 1


@mark.asyncio
@mark.parametrize(
    "distance_function, expected_similar_score, expected_dissimilar_score",
    [
        (DistanceFunction.COSINE_DISTANCE, 0.0, 2.0),
        (DistanceFunction.COSINE_SIMILARITY, 1.0, -1.0),
        (DistanceFunction.EUCLIDEAN_DISTANCE, 0.0, 4.47213595499958),
        (DistanceFunction.MANHATTAN, 0.0, 10.0),
        (DistanceFunction.EUCLIDEAN_SQUARED_DISTANCE, 0.0, 20.0),
        (DistanceFunction.DOT_PROD, 5.0, -5.0),
        (DistanceFunction.HAMMING, 0.0, 1.0),
    ],
)
async def test_vectorized_search_similar(
    collection, distance_function, expected_similar_score, expected_dissimilar_score
):
    collection.data_model_definition.fields["vector"].distance_function = distance_function
    record = {"id": "testid", "content": "test content", "vector": [1.0, 1.0, 1.0, 1.0, 1.0]}
    await collection.upsert(record)
    results = await collection.vectorized_search(
        vector=[1.0, 1.0, 1.0, 1.0, 1.0], options=VectorSearchOptions(vector_field_name="vector")
    )
    async for res in results.results:
        assert res.score == expected_similar_score
        assert res.record == record
    results = await collection.vectorized_search(
        vector=[-1.0, -1.0, -1.0, -1.0, -1.0], options=VectorSearchOptions(vector_field_name="vector")
    )
    async for res in results.results:
        assert res.score == expected_dissimilar_score
        assert res.record == record
