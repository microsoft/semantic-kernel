# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import MagicMock, patch

from pytest import fixture, mark, raises
from qdrant_client.async_qdrant_client import AsyncQdrantClient
from qdrant_client.models import Datatype, Distance, FieldCondition, Filter, MatchAny, VectorParams

from semantic_kernel.connectors.memory.qdrant.qdrant_collection import QdrantCollection
from semantic_kernel.connectors.memory.qdrant.qdrant_store import QdrantStore
from semantic_kernel.data.record_definition import VectorStoreRecordVectorField
from semantic_kernel.data.vector_search import VectorSearchFilter, VectorSearchOptions
from semantic_kernel.exceptions import (
    VectorSearchExecutionException,
    VectorStoreInitializationException,
    VectorStoreModelValidationError,
    VectorStoreOperationException,
)

BASE_PATH = "qdrant_client.async_qdrant_client.AsyncQdrantClient"


@fixture
def vector_store(qdrant_unit_test_env):
    return QdrantStore(env_file_path="test.env")


@fixture
def collection(qdrant_unit_test_env, data_model_definition):
    return QdrantCollection(
        data_model_type=dict,
        collection_name="test",
        data_model_definition=data_model_definition,
        env_file_path="test.env",
    )


@fixture
def collection_without_named_vectors(qdrant_unit_test_env, data_model_definition):
    return QdrantCollection(
        data_model_type=dict,
        collection_name="test",
        data_model_definition=data_model_definition,
        named_vectors=False,
        env_file_path="test.env",
    )


@fixture(autouse=True)
def mock_list_collection_names():
    with patch(f"{BASE_PATH}.get_collections") as mock_get_collections:
        from qdrant_client.conversions.common_types import CollectionsResponse
        from qdrant_client.http.models import CollectionDescription

        response = MagicMock(spec=CollectionsResponse)
        response.collections = [CollectionDescription(name="test")]
        mock_get_collections.return_value = response
        yield mock_get_collections


@fixture(autouse=True)
def mock_does_collection_exist():
    with patch(f"{BASE_PATH}.collection_exists") as mock_collection_exists:
        mock_collection_exists.return_value = True
        yield mock_collection_exists


@fixture(autouse=True)
def mock_create_collection():
    with patch(f"{BASE_PATH}.create_collection") as mock_recreate_collection:
        yield mock_recreate_collection


@fixture(autouse=True)
def mock_delete_collection():
    with patch(f"{BASE_PATH}.delete_collection") as mock_delete_collection:
        mock_delete_collection.return_value = True
        yield mock_delete_collection


@fixture(autouse=True)
def mock_upsert():
    with patch(f"{BASE_PATH}.upsert") as mock_upsert:
        from qdrant_client.conversions.common_types import UpdateResult

        result = MagicMock(spec=UpdateResult)
        result.status = "completed"
        mock_upsert.return_value = result
        yield mock_upsert


@fixture(autouse=True)
def mock_get(collection):
    with patch(f"{BASE_PATH}.retrieve") as mock_retrieve:
        from qdrant_client.http.models import Record

        if collection.named_vectors:
            mock_retrieve.return_value = [
                Record(id="id1", payload={"content": "content"}, vector={"vector": [1.0, 2.0, 3.0]})
            ]
        else:
            mock_retrieve.return_value = [Record(id="id1", payload={"content": "content"}, vector=[1.0, 2.0, 3.0])]
        yield mock_retrieve


@fixture(autouse=True)
def mock_delete():
    with patch(f"{BASE_PATH}.delete") as mock_delete:
        yield mock_delete


@fixture(autouse=True)
def mock_search():
    with patch(f"{BASE_PATH}.search") as mock_search:
        from qdrant_client.models import ScoredPoint

        response1 = ScoredPoint(id="id1", version=1, score=0.0, payload={"content": "content"})
        response2 = ScoredPoint(id="id2", version=1, score=0.0, payload={"content": "content"})
        mock_search.return_value = [response1, response2]
        yield mock_search


async def test_vector_store_defaults(vector_store):
    async with vector_store:
        assert vector_store.qdrant_client is not None
        assert vector_store.qdrant_client._client.rest_uri == "http://localhost:6333"


def test_vector_store_with_client():
    qdrant_store = QdrantStore(client=AsyncQdrantClient())
    assert qdrant_store.qdrant_client is not None
    assert qdrant_store.qdrant_client._client.rest_uri == "http://localhost:6333"


@mark.parametrize("exclude_list", [["QDRANT_LOCATION"]], indirect=True)
def test_vector_store_in_memory(qdrant_unit_test_env):
    from qdrant_client.local.async_qdrant_local import AsyncQdrantLocal

    qdrant_store = QdrantStore(api_key="supersecretkey", env_file_path="test.env")
    assert qdrant_store.qdrant_client is not None
    assert isinstance(qdrant_store.qdrant_client._client, AsyncQdrantLocal)
    assert qdrant_store.qdrant_client._client.location == ":memory:"


def test_vector_store_fail():
    with raises(VectorStoreInitializationException, match="Failed to create Qdrant settings."):
        QdrantStore(location="localhost", url="localhost", env_file_path="test.env")

    with raises(VectorStoreInitializationException, match="Failed to create Qdrant client."):
        QdrantStore(location="localhost", url="http://localhost", env_file_path="test.env")


async def test_store_list_collection_names(vector_store):
    collections = await vector_store.list_collection_names()
    assert collections == ["test"]


def test_get_collection(vector_store, data_model_definition, qdrant_unit_test_env):
    collection = vector_store.get_collection("test", data_model_type=dict, data_model_definition=data_model_definition)
    assert collection.collection_name == "test"
    assert collection.qdrant_client == vector_store.qdrant_client
    assert collection.data_model_type is dict
    assert collection.data_model_definition == data_model_definition
    assert vector_store.vector_record_collections["test"] == collection


async def test_collection_init(data_model_definition, qdrant_unit_test_env):
    async with QdrantCollection(
        data_model_type=dict,
        collection_name="test",
        data_model_definition=data_model_definition,
        env_file_path="test.env",
    ) as collection:
        assert collection.collection_name == "test"
        assert collection.qdrant_client is not None
        assert collection.data_model_type is dict
        assert collection.data_model_definition == data_model_definition
        assert collection.named_vectors


def test_collection_init_fail(data_model_definition):
    with raises(VectorStoreInitializationException, match="Failed to create Qdrant settings."):
        QdrantCollection(
            data_model_type=dict,
            collection_name="test",
            data_model_definition=data_model_definition,
            url="localhost",
            env_file_path="test.env",
        )
    with raises(VectorStoreInitializationException, match="Failed to create Qdrant client."):
        QdrantCollection(
            data_model_type=dict,
            collection_name="test",
            data_model_definition=data_model_definition,
            location="localhost",
            url="http://localhost",
            env_file_path="test.env",
        )
    with raises(
        VectorStoreModelValidationError, match="Only one vector field is allowed when not using named vectors."
    ):
        data_model_definition.fields["vector2"] = VectorStoreRecordVectorField(name="vector2", dimensions=3)
        QdrantCollection(
            data_model_type=dict,
            collection_name="test",
            data_model_definition=data_model_definition,
            named_vectors=False,
            env_file_path="test.env",
        )


@mark.parametrize("collection_to_use", ["collection", "collection_without_named_vectors"])
async def test_upsert(collection_to_use, request):
    from qdrant_client.models import PointStruct

    collection = request.getfixturevalue(collection_to_use)
    if collection.named_vectors:
        record = PointStruct(id="id1", payload={"content": "content"}, vector={"vector": [1.0, 2.0, 3.0]})
    else:
        record = PointStruct(id="id1", payload={"content": "content"}, vector=[1.0, 2.0, 3.0])
    ids = await collection._inner_upsert([record])
    assert ids[0] == "id1"

    ids = await collection.upsert(record={"id": "id1", "content": "content", "vector": [1.0, 2.0, 3.0]})
    assert ids == "id1"


async def test_get(collection):
    records = await collection._inner_get(["id1"])
    assert records is not None

    records = await collection.get("id1")
    assert records is not None


async def test_delete(collection):
    await collection._inner_delete(["id1"])


async def test_does_collection_exist(collection):
    await collection.does_collection_exist()


async def test_delete_collection(collection):
    await collection.delete_collection()


@mark.parametrize(
    "collection_to_use, results",
    [
        (
            "collection",
            {
                "collection_name": "test",
                "vectors_config": {"vector": VectorParams(size=5, distance=Distance.COSINE, datatype=Datatype.FLOAT32)},
            },
        ),
        (
            "collection_without_named_vectors",
            {
                "collection_name": "test",
                "vectors_config": VectorParams(size=5, distance=Distance.COSINE, datatype=Datatype.FLOAT32),
            },
        ),
    ],
)
async def test_create_index_with_named_vectors(collection_to_use, results, mock_create_collection, request):
    await request.getfixturevalue(collection_to_use).create_collection()
    mock_create_collection.assert_called_once_with(**results)


@mark.parametrize("collection_to_use", ["collection", "collection_without_named_vectors"])
async def test_create_index_fail(collection_to_use, request):
    collection = request.getfixturevalue(collection_to_use)
    collection.data_model_definition.fields["vector"].dimensions = None
    with raises(VectorStoreOperationException, match="Vector field must have dimensions."):
        await collection.create_collection()


async def test_search(collection, mock_search):
    results = await collection._inner_search(vector=[1.0, 2.0, 3.0], options=VectorSearchOptions(include_vectors=False))
    async for result in results.results:
        assert result.record["id"] == "id1"
        break

    assert mock_search.call_count == 1
    mock_search.assert_called_with(
        collection_name="test",
        query_vector=[1.0, 2.0, 3.0],
        query_filter=Filter(must=[]),
        with_vectors=False,
        limit=3,
        offset=0,
    )


async def test_search_named_vectors(collection, mock_search):
    collection.named_vectors = True
    results = await collection._inner_search(
        vector=[1.0, 2.0, 3.0], options=VectorSearchOptions(vector_field_name="vector", include_vectors=False)
    )
    async for result in results.results:
        assert result.record["id"] == "id1"
        break

    assert mock_search.call_count == 1
    mock_search.assert_called_with(
        collection_name="test",
        query_vector=("vector", [1.0, 2.0, 3.0]),
        query_filter=Filter(must=[]),
        with_vectors=False,
        limit=3,
        offset=0,
    )


async def test_search_filter(collection, mock_search):
    results = await collection._inner_search(
        vector=[1.0, 2.0, 3.0],
        options=VectorSearchOptions(include_vectors=False, filter=VectorSearchFilter.equal_to("id", "id1")),
    )
    async for result in results.results:
        assert result.record["id"] == "id1"
        break

    assert mock_search.call_count == 1
    mock_search.assert_called_with(
        collection_name="test",
        query_vector=[1.0, 2.0, 3.0],
        query_filter=Filter(must=[FieldCondition(key="id", match=MatchAny(any=["id1"]))]),
        with_vectors=False,
        limit=3,
        offset=0,
    )


async def test_search_fail(collection):
    with raises(VectorSearchExecutionException, match="Search requires a vector."):
        await collection._inner_search(options=VectorSearchOptions(include_vectors=False))
