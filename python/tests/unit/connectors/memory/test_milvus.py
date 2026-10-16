# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import MagicMock, patch

from pymilvus import MilvusClient
from pytest import fixture, mark, raises

from semantic_kernel.connectors.milvus import MilvusCollection, MilvusStore
from semantic_kernel.data.vector import DistanceFunction, VectorStoreField
from semantic_kernel.exceptions import (
    VectorSearchExecutionException,
    VectorStoreInitializationException,
    VectorStoreOperationException,
)

BASE_PATH = "semantic_kernel.connectors.milvus.MilvusClient"


@fixture
def mock_client():
    """A MagicMock standing in for a pymilvus MilvusClient."""
    client = MagicMock(spec=MilvusClient)
    client.has_collection.return_value = True
    client.list_collections.return_value = ["test"]
    client.get.return_value = [{"id": "id1", "content": "content", "vector": [1.0, 2.0, 3.0, 4.0, 5.0]}]
    client.search.return_value = [
        [
            {"id": "id1", "distance": 0.1, "entity": {"content": "content"}},
            {"id": "id2", "distance": 0.2, "entity": {"content": "content"}},
        ]
    ]
    return client


@fixture
def vector_store(mock_client):
    return MilvusStore(client=mock_client)


@fixture
def collection(definition, mock_client):
    return MilvusCollection(
        record_type=dict,
        collection_name="test",
        definition=definition,
        client=mock_client,
    )


def test_vector_store_with_client(mock_client):
    store = MilvusStore(client=mock_client)
    assert store.milvus_client is mock_client
    assert store.managed_client is False


def test_vector_store_from_settings(milvus_unit_test_env):
    with patch(BASE_PATH) as mock_milvus_client:
        mock_milvus_client.return_value = MagicMock(spec=MilvusClient)
        store = MilvusStore(env_file_path="test.env")
        assert store.milvus_client is not None
        mock_milvus_client.assert_called_once()
        assert mock_milvus_client.call_args.kwargs["uri"] == "http://localhost:19530"


def test_vector_store_fail():
    with (
        raises(VectorStoreInitializationException, match="Failed to create Milvus client."),
        patch(BASE_PATH, side_effect=ValueError("boom")),
    ):
        MilvusStore(uri="http://localhost:19530")


async def test_store_list_collection_names(vector_store):
    collections = await vector_store.list_collection_names()
    assert collections == ["test"]


def test_get_collection(vector_store, definition):
    collection = vector_store.get_collection(collection_name="test", record_type=dict, definition=definition)
    assert collection.collection_name == "test"
    assert collection.milvus_client is vector_store.milvus_client
    assert collection.record_type is dict
    assert collection.definition == definition


def test_collection_with_client(collection, mock_client):
    assert collection.collection_name == "test"
    assert collection.milvus_client is mock_client
    assert collection.managed_client is False


def test_collection_from_settings(definition, milvus_unit_test_env):
    with patch(BASE_PATH) as mock_milvus_client:
        mock_milvus_client.return_value = MagicMock(spec=MilvusClient)
        collection = MilvusCollection(
            record_type=dict,
            collection_name="test",
            definition=definition,
            env_file_path="test.env",
        )
        assert collection.milvus_client is not None
        assert collection.managed_client is True


async def test_upsert(collection, mock_client):
    ids = await collection._inner_upsert([{"id": "id1", "content": "content", "vector": [1.0, 2.0, 3.0, 4.0, 5.0]}])
    assert ids == ["id1"]

    ids = await collection.upsert(records={"id": "id1", "content": "content", "vector": [1.0, 2.0, 3.0, 4.0, 5.0]})
    assert ids == "id1"
    mock_client.upsert.assert_called()


async def test_get(collection, mock_client):
    records = await collection._inner_get(["id1"])
    assert records is not None
    mock_client.get.assert_called_once()

    record = await collection.get("id1")
    assert record is not None


async def test_get_without_keys_returns_none(collection):
    assert await collection._inner_get(None) is None


async def test_delete(collection, mock_client):
    await collection._inner_delete(["id1"])
    mock_client.delete.assert_called_once()


async def test_collection_exists(collection, mock_client):
    assert await collection.collection_exists() is True
    mock_client.has_collection.assert_called_with("test")


async def test_ensure_collection_exists_skips_when_present(collection, mock_client):
    mock_client.has_collection.return_value = True
    await collection.ensure_collection_exists()
    mock_client.create_collection.assert_not_called()


async def test_ensure_collection_exists_creates_when_absent(collection, mock_client):
    mock_client.has_collection.return_value = False
    await collection.ensure_collection_exists()
    mock_client.create_collection.assert_called_once()
    assert mock_client.create_collection.call_args.kwargs["collection_name"] == "test"


async def test_ensure_collection_exists_bad_index_fails(collection, mock_client):
    from semantic_kernel.data.vector import IndexKind

    mock_client.has_collection.return_value = False
    for field in collection.definition.vector_fields:
        field.index_kind = IndexKind.QUANTIZED_FLAT
    with raises(VectorStoreOperationException):
        await collection.ensure_collection_exists()


async def test_ensure_collection_deleted(collection, mock_client):
    mock_client.has_collection.return_value = True
    await collection.ensure_collection_deleted()
    mock_client.drop_collection.assert_called_once_with("test")


async def test_search(collection, mock_client):
    results = await collection.search(vector=[1.0, 2.0, 3.0, 4.0, 5.0], include_vectors=False)
    returned = [result async for result in results.results]
    assert returned[0].record["id"] == "id1"
    assert returned[0].score == 0.1
    assert mock_client.search.call_count == 1
    assert mock_client.search.call_args.kwargs["anns_field"] == "vector"
    assert mock_client.search.call_args.kwargs["search_params"]["metric_type"] == "COSINE"


async def test_search_filter(collection, mock_client):
    results = await collection.search(
        vector=[1.0, 2.0, 3.0, 4.0, 5.0],
        include_vectors=False,
        filter=lambda x: x.content == "content",
    )
    _ = [result async for result in results.results]
    assert mock_client.search.call_args.kwargs["filter"] == '(content == "content")'


async def test_search_fail(collection):
    with raises(VectorSearchExecutionException, match="Search requires a vector."):
        await collection.search(include_vectors=False)


@mark.parametrize(
    "expression, expected",
    [
        (lambda x: x.content == "a", '(content == "a")'),
        (lambda x: x.content != "a", '(content != "a")'),
        (lambda x: x.content in ["a", "b"], '(content in ["a", "b"])'),
        (lambda x: x.content not in ["a", "b"], '(content not in ["a", "b"])'),
        (lambda x: not (x.content == "a" and x.id == "b"), '(not ((content == "a") and (id == "b")))'),
        (lambda x: x.content == "a" and x.id == "b", '((content == "a") and (id == "b"))'),
        (lambda x: x.content == "a" or x.id == "b", '((content == "a") or (id == "b"))'),
    ],
)
def test_filter_translation(collection, expression, expected):
    assert collection._build_filter(expression) == expected


def test_distance_function_mapping(collection):
    from semantic_kernel.connectors.milvus import DISTANCE_FUNCTION_MAP

    assert DISTANCE_FUNCTION_MAP[DistanceFunction.COSINE_SIMILARITY] == "COSINE"
    assert DISTANCE_FUNCTION_MAP[DistanceFunction.EUCLIDEAN_DISTANCE] == "L2"
    assert DISTANCE_FUNCTION_MAP[DistanceFunction.DOT_PROD] == "IP"


def test_no_vector_field_fails(mock_client):
    from semantic_kernel.data.vector import VectorStoreCollectionDefinition
    from semantic_kernel.exceptions import VectorStoreModelValidationError

    definition = VectorStoreCollectionDefinition(
        fields=[
            VectorStoreField("key", name="id"),
            VectorStoreField("data", name="content"),
        ]
    )
    with raises(VectorStoreModelValidationError):
        MilvusCollection(record_type=dict, collection_name="test", definition=definition, client=mock_client)
