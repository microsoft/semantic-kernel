# Copyright (c) Microsoft. All rights reserved.

from typing import Any
from unittest.mock import AsyncMock, Mock, patch

from pinecone import FetchResponse, IndexModel, Metric, QueryResponse, ServerlessSpec, Vector
from pinecone.core.openapi.db_data.models import (
    Hit,
    ScoredVector,
    SearchRecordsResponse,
    SearchRecordsResponseResult,
    SearchUsage,
)
from pinecone.data.index_asyncio import _IndexAsyncio
from pytest import fixture, mark, raises

from semantic_kernel.connectors.memory.pinecone import PineconeStore
from semantic_kernel.connectors.memory.pinecone._pinecone import PineconeCollection
from semantic_kernel.data.vector_search import VectorSearchFilter, VectorSearchOptions
from semantic_kernel.exceptions.vector_store_exceptions import VectorStoreInitializationException

BASE_PATH_ASYNCIO = "pinecone.PineconeAsyncio"
BASE_PATH_INDEX_CLIENT_ASYNCIO = "pinecone.data.index_asyncio._IndexAsyncio"


@fixture
def embed(request) -> dict[str, Any] | None:
    if hasattr(request, "param"):
        return request.param
    return None


@fixture
def mock_index_model(embed: dict[str, Any] | None):
    """Mock IndexModel for testing."""
    mock_index_model = Mock(spec=IndexModel)
    mock_index_model.name = "test"
    mock_index_model.embed = embed
    mock_index_model.host = "test_host"
    return mock_index_model


@fixture(autouse=True)
def mock_list_collection_names(mock_index_model):
    with patch(f"{BASE_PATH_ASYNCIO}.list_indexes") as mock_list_indexes:
        mock_list_indexes.return_value = [mock_index_model]
        yield mock_list_indexes


@fixture(autouse=True)
def mock_create_index(mock_index_model):
    with patch(f"{BASE_PATH_ASYNCIO}.create_index") as mock_create_index:
        mock_create_index.return_value = mock_index_model
        yield mock_create_index


@fixture(autouse=True)
def mock_create_index_for_model(mock_index_model):
    with patch(f"{BASE_PATH_ASYNCIO}.create_index_for_model") as mock_create_index_for_model:
        mock_create_index_for_model.return_value = mock_index_model
        yield mock_create_index_for_model


@fixture(autouse=True)
def mock_describe_index(mock_index_model):
    with patch(f"{BASE_PATH_ASYNCIO}.describe_index") as mock_describe_index:
        mock_describe_index.return_value = mock_index_model
        yield mock_describe_index


@fixture(autouse=True)
def mock_has_index():
    with patch(f"{BASE_PATH_ASYNCIO}.has_index") as mock_has_index:
        mock_create_index.return_value = True
        yield mock_has_index


@fixture(autouse=True)
def mock_index_asyncio():
    mock_index_asyncio = AsyncMock(spec=_IndexAsyncio)
    mock_index_asyncio.close.return_value = None
    with patch(f"{BASE_PATH_ASYNCIO}.IndexAsyncio") as mock_index:
        mock_index.return_value = mock_index_asyncio
        yield mock_index


@fixture(autouse=True)
def mock_delete_index():
    with patch(f"{BASE_PATH_ASYNCIO}.delete_index") as mock_delete:
        yield mock_delete


@fixture
async def store(pinecone_unit_test_env) -> PineconeStore:
    """Fixture to create a Pinecone store."""
    async with PineconeStore() as store:
        yield store


@fixture
async def collection(pinecone_unit_test_env, data_model_definition) -> PineconeCollection:
    """Fixture to create a Pinecone store."""
    async with PineconeCollection(
        collection_name="test_collection",
        data_model_type=dict,
        data_model_definition=data_model_definition,
    ) as collection:
        yield collection


async def test_create_store(pinecone_unit_test_env):
    """Test the creation of a Pinecone store."""
    # Create a Pinecone store
    store = PineconeStore()
    assert store is not None
    assert store.client is not None


@mark.parametrize("exclude_list", [["PINECONE_API_KEY"]], indirect=True)
async def test_create_store_fail(pinecone_unit_test_env):
    """Test the creation of a Pinecone store."""
    with raises(VectorStoreInitializationException):
        PineconeStore(env_file_path="test.env")


def test_create_store_grpc(pinecone_unit_test_env):
    """Test the creation of a Pinecone store."""

    # Create a Pinecone store
    store = PineconeStore(use_grpc=True)
    assert store is not None
    assert store.client is not None


@mark.parametrize("exclude_list", [["PINECONE_API_KEY"]], indirect=True)
async def test_create_collection_fail(pinecone_unit_test_env, data_model_definition):
    with raises(VectorStoreInitializationException):
        PineconeCollection(
            collection_name="test_collection",
            data_model_type=dict,
            data_model_definition=data_model_definition,
            env_file_path="test.env",
        )


async def test_get_collection(store, data_model_definition):
    """Test the creation of a Pinecone collection."""
    # Create a collection
    collection = store.get_collection("test_collection", dict, data_model_definition)
    assert collection is not None
    assert collection.collection_name == "test_collection"


async def test_list_collection_names(store):
    """Test the listing of Pinecone collections."""
    # List collections
    collections = await store.list_collection_names()
    assert collections is not None
    assert len(collections) == 1
    assert collections[0] == "test"


@mark.parametrize("embed", [None, {"model": "test-model"}])
async def test_load_index_client(collection, mock_index_asyncio):
    # Test loading the index client
    await collection._load_index_client()
    assert collection.index is not None
    assert collection.index_client is not None
    assert isinstance(collection.index_client, _IndexAsyncio)
    assert collection.embed_settings == collection.index.embed


async def test_create_collection(collection, mock_create_index):
    await collection.create_collection()
    assert collection.index is not None
    assert collection.index_client is not None
    mock_create_index.assert_awaited_once_with(
        name=collection.collection_name,
        spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        dimension=5,
        metric=Metric.COSINE,
        vector_type="dense",
    )


@mark.parametrize("embed", [{"model": "test-model"}])
async def test_create_collection_integrated(collection, mock_create_index_for_model):
    await collection.create_collection(embed={"model": "test-model"})
    assert collection.index is not None
    assert collection.index_client is not None
    mock_create_index_for_model.assert_awaited_once_with(
        name=collection.collection_name,
        cloud="aws",
        region="us-east-1",
        embed={"model": "test-model", "metric": Metric.COSINE, "field_map": {"text": "content"}},
    )


async def test_delete_collection(collection):
    # Test deleting the collection
    await collection.delete_collection()
    assert collection.index is None
    assert collection.index_client is None


async def test_upsert(collection):
    record = {
        "id": "test_id",
        "vector": [0.1, 0.2, 0.3, 0.4, 0.5],
        "content": "test_content",
    }
    pinecone_vector = Vector(values=record["vector"], id=record["id"], metadata={"content": record["content"]})
    await collection._load_index_client()
    with patch.object(collection.index_client, "upsert", new_callable=AsyncMock) as mock_upsert:
        await collection.upsert(record)
        mock_upsert.assert_awaited_once_with(
            [pinecone_vector],
            namespace=collection.namespace,
        )


@mark.parametrize("embed", [{"model": "test-model"}])
async def test_upsert_embed(collection):
    record = {
        "id": "test_id",
        "content": "test_content",
        "vector": [0.1, 0.2, 0.3, 0.4, 0.5],
    }
    await collection._load_index_client()
    with patch.object(collection.index_client, "upsert_records", new_callable=AsyncMock) as mock_upsert:
        await collection.upsert(record)
        mock_upsert.assert_awaited_once_with(
            records=[{"_id": record["id"], "content": record["content"]}],
            namespace=collection.namespace,
        )


async def test_get(collection):
    record = {
        "id": "test_id",
        "vector": [0.1, 0.2, 0.3, 0.4, 0.5],
        "content": "test_content",
    }
    fetch_response = FetchResponse(
        namespace="",
        vectors={
            record["id"]: Vector(values=record["vector"], id=record["id"], metadata={"content": record["content"]})
        },
        usage={},
    )
    await collection._load_index_client()
    with patch.object(collection.index_client, "fetch", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = fetch_response
        get_record = await collection.get(record["id"])
        mock_fetch.assert_awaited_once_with(
            ids=[record["id"]],
            namespace=collection.namespace,
        )
        assert record == get_record


async def test_delete(collection):
    await collection._load_index_client()
    with patch.object(collection.index_client, "delete", new_callable=AsyncMock) as mock_delete:
        await collection.delete("test_id")
        mock_delete.assert_awaited_once_with(
            ids=["test_id"],
            namespace=collection.namespace,
        )


async def test_search(collection):
    record = {
        "id": "test_id",
        "vector": [0.1, 0.2, 0.3, 0.4, 0.5],
        "content": "test_content",
    }
    query_response = QueryResponse._from_openapi_data(
        namespace="",
        matches=[
            ScoredVector(**{
                "values": record["vector"],
                "id": record["id"],
                "metadata": {"content": record["content"]},
                "score": 0.1,
            })
        ],
    )
    await collection._load_index_client()
    with patch.object(collection.index_client, "query", new_callable=AsyncMock) as mock_query:
        mock_query.return_value = query_response
        query_response = await collection.vectorized_search(
            vector=[0.1, 0.2, 0.3, 0.4, 0.5],
            options=VectorSearchOptions(
                top=1, include_vectors=True, filter=VectorSearchFilter.equal_to("content", "test_content")
            ),
        )
        mock_query.assert_awaited_once_with(
            vector=[0.1, 0.2, 0.3, 0.4, 0.5],
            top_k=1,
            include_metadata=True,
            include_values=True,
            namespace=collection.namespace,
            filter={"content": {"$eq": "test_content"}},
        )
        assert query_response.total_count == 1
        async for result in query_response.results:
            assert result.record == record
            assert result.score == 0.1


@mark.parametrize("embed", [{"model": "test-model"}])
async def test_search_embed(collection):
    record = {"id": "test_id", "content": "test_content", "vector": None}
    query_response = SearchRecordsResponse._from_openapi_data(
        result=SearchRecordsResponseResult._from_openapi_data(**{
            "hits": [
                Hit(**{
                    "_id": record["id"],
                    "fields": {"id": record["id"], "content": record["content"]},
                    "_score": 0.1,
                })
            ]
        }),
        usage=SearchUsage(read_units=0),
    )
    await collection._load_index_client()
    with patch.object(collection.index_client, "search_records", new_callable=AsyncMock) as mock_query:
        mock_query.return_value = query_response
        query_response = await collection.vectorizable_text_search(
            vectorizable_text="test", options=VectorSearchOptions(top=1, include_vectors=True)
        )
        mock_query.assert_awaited_once_with(
            query={"inputs": {"text": "test"}, "top_k": 1, "filter": {}},
            namespace=collection.namespace,
        )
        assert query_response.total_count == 1
        async for result in query_response.results:
            assert result.record == record
            assert result.score == 0.1
