# Copyright (c) Microsoft. All rights reserved.

from pytest import fixture, mark, raises

from semantic_kernel.connectors.in_memory import InMemoryCollection, InMemoryStore
from semantic_kernel.data.vector import DistanceFunction
from semantic_kernel.exceptions.vector_store_exceptions import VectorStoreOperationException


@fixture
def collection(definition):
    return InMemoryCollection(collection_name="test", record_type=dict, definition=definition)


def test_store_init():
    store = InMemoryStore()
    assert store is not None


def test_store_get_collection(definition):
    store = InMemoryStore()
    collection = store.get_collection(collection_name="test", record_type=dict, definition=definition)
    assert collection.collection_name == "test"
    assert collection.record_type is dict
    assert collection.definition == definition


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
    await collection.ensure_collection_deleted()
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
    for field in collection.definition.fields:
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


async def test_valid_lambda_filter(collection):
    record1 = {"id": "1", "vector": [1, 2, 3, 4, 5]}
    record2 = {"id": "2", "vector": [5, 4, 3, 2, 1]}
    await collection.upsert([record1, record2])
    # Filter to select only record with id == '1'
    results = collection._get_filtered_records(type("opt", (), {"filter": "lambda x: x.id == '1'"})())
    assert len(results) == 1
    assert "1" in results


async def test_valid_lambda_filter_attribute_access(collection):
    record1 = {"id": "1", "vector": [1, 2, 3, 4, 5]}
    record2 = {"id": "2", "vector": [5, 4, 3, 2, 1]}
    await collection.upsert([record1, record2])
    # Filter to select only record with id == '2' using attribute access
    results = collection._get_filtered_records(type("opt", (), {"filter": "lambda x: x['id'] == '2'"})())
    assert len(results) == 1
    assert "2" in results


async def test_invalid_filter_not_lambda(collection):
    with raises(VectorStoreOperationException, match="must be a lambda expression"):
        collection._get_filtered_records(type("opt", (), {"filter": "x.id == '1'"})())


async def test_invalid_filter_syntax(collection):
    with raises(VectorStoreOperationException, match="not valid Python"):
        collection._get_filtered_records(type("opt", (), {"filter": "lambda x: x.id == '1' and"})())


async def test_malicious_filter_import(collection):
    # Should not allow import statement
    with raises(VectorStoreOperationException):
        collection._get_filtered_records(
            type("opt", (), {"filter": "lambda x: __import__('os').system('echo malicious')"})()
        )


async def test_malicious_filter_exec(collection):
    # Should not allow exec or similar
    with raises(VectorStoreOperationException):
        collection._get_filtered_records(type("opt", (), {"filter": "lambda x: exec('print(1)')"})())


async def test_malicious_filter_builtins(collection):
    # Should not allow access to builtins
    with raises(VectorStoreOperationException):
        collection._get_filtered_records(
            type("opt", (), {"filter": "lambda x: __builtins__.__import__('os').system('echo malicious')"})()
        )


async def test_malicious_filter_open(collection):
    # Should not allow open()
    with raises(VectorStoreOperationException):
        collection._get_filtered_records(type("opt", (), {"filter": "lambda x: open('somefile.txt', 'w')"})())


async def test_malicious_filter_eval(collection):
    # Should not allow eval()
    with raises(VectorStoreOperationException):
        collection._get_filtered_records(type("opt", (), {"filter": "lambda x: eval('2+2')"})())


async def test_multiple_filters(collection):
    record1 = {"id": "1", "vector": [1, 2, 3, 4, 5]}
    record2 = {"id": "2", "vector": [5, 4, 3, 2, 1]}
    await collection.upsert([record1, record2])
    filters = ["lambda x: x.id == '1'", "lambda x: x.vector[0] == 1"]
    results = collection._get_filtered_records(type("opt", (), {"filter": filters})())
    assert len(results) == 1
    assert "1" in results
