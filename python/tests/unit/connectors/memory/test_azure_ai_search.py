# Copyright (c) Microsoft. All rights reserved.


import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import numpy as np
from azure.search.documents.aio import SearchClient
from azure.search.documents.indexes.aio import SearchIndexClient
from pytest import fixture, mark, param, raises

from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.azure_ai_search import (
    AzureAISearchCollection,
    AzureAISearchSettings,
    AzureAISearchStore,
    _definition_to_azure_ai_search_index,
    _get_search_index_client,
)
from semantic_kernel.exceptions import (
    ServiceInitializationError,
    VectorStoreInitializationException,
    VectorStoreOperationException,
)
from semantic_kernel.utils.list_handler import desync_list
from tests.unit.connectors.memory.conftest import filter_lambda_list

BASE_PATH_SEARCH_CLIENT = "azure.search.documents.aio.SearchClient"
BASE_PATH_INDEX_CLIENT = "azure.search.documents.indexes.aio.SearchIndexClient"


@fixture
def vector_store(azure_ai_search_unit_test_env):
    """Fixture to instantiate AzureCognitiveSearchMemoryStore with basic configuration."""
    return AzureAISearchStore()


@fixture
def mock_create_collection():
    """Fixture to patch 'SearchIndexClient' and its 'create_index' method."""
    with patch(f"{BASE_PATH_INDEX_CLIENT}.create_index") as mock_create_index:
        yield mock_create_index


@fixture
def mock_delete_collection():
    """Fixture to patch 'SearchIndexClient' and its 'create_index' method."""
    with patch(f"{BASE_PATH_INDEX_CLIENT}.delete_index") as mock_delete_index:
        yield mock_delete_index


@fixture
def mock_list_collection_names():
    """Fixture to patch 'SearchIndexClient' and its 'create_index' method."""
    with patch(f"{BASE_PATH_INDEX_CLIENT}.list_index_names") as mock_list_index_names:
        # Setup the mock to return a specific SearchIndex instance when called
        mock_list_index_names.return_value = desync_list(["test"])
        yield mock_list_index_names


@fixture
def mock_upsert():
    with patch(f"{BASE_PATH_SEARCH_CLIENT}.merge_or_upload_documents") as mock_merge_or_upload_documents:
        from azure.search.documents.models import IndexingResult

        result = MagicMock(spec=IndexingResult)
        result.key = "id1"
        mock_merge_or_upload_documents.return_value = [result]
        yield mock_merge_or_upload_documents


@fixture
def mock_get():
    with patch(f"{BASE_PATH_SEARCH_CLIENT}.get_document") as mock_get_document:
        mock_get_document.return_value = {"id": "id1", "content": "content", "vector": [1.0, 2.0, 3.0]}
        yield mock_get_document


@fixture
def mock_search():
    async def iter_search_results(*args, **kwargs):
        yield {"id": "id1", "content": "content", "vector": [1.0, 2.0, 3.0]}
        await asyncio.sleep(0.0)

    with patch(f"{BASE_PATH_SEARCH_CLIENT}.search") as mock_search:
        mock_search.side_effect = iter_search_results
        yield mock_search


@fixture
def mock_delete():
    with patch(f"{BASE_PATH_SEARCH_CLIENT}.delete_documents") as mock_delete_documents:
        yield mock_delete_documents


@fixture
def collection(azure_ai_search_unit_test_env, definition):
    return AzureAISearchCollection(record_type=dict, definition=definition)


async def test_init(azure_ai_search_unit_test_env, definition):
    async with AzureAISearchCollection(record_type=dict, definition=definition) as collection:
        assert collection is not None
        assert collection.record_type is dict
        assert collection.definition == definition
        assert collection.collection_name == "test-index-name"
        assert collection.search_index_client is not None
        assert collection.search_client is not None


def test_init_with_type(azure_ai_search_unit_test_env, record_type):
    collection = AzureAISearchCollection(record_type=record_type)
    assert collection is not None
    assert collection.record_type is record_type
    assert collection.collection_name == "test-index-name"
    assert collection.search_index_client is not None
    assert collection.search_client is not None


@mark.parametrize("exclude_list", [["AZURE_AI_SEARCH_ENDPOINT"]], indirect=True)
def test_init_endpoint_fail(azure_ai_search_unit_test_env, definition):
    with raises(VectorStoreInitializationException):
        AzureAISearchCollection(record_type=dict, definition=definition, env_file_path="test.env")


@mark.parametrize("exclude_list", [["AZURE_AI_SEARCH_INDEX_NAME"]], indirect=True)
def test_init_index_fail(azure_ai_search_unit_test_env, definition):
    with raises(VectorStoreInitializationException):
        AzureAISearchCollection(record_type=dict, definition=definition, env_file_path="test.env")


def test_init_with_clients(azure_ai_search_unit_test_env, definition):
    search_index_client = MagicMock(spec=SearchIndexClient)
    search_client = MagicMock(spec=SearchClient)
    search_client._index_name = "test-index-name"

    collection = AzureAISearchCollection(
        record_type=dict,
        definition=definition,
        search_index_client=search_index_client,
        search_client=search_client,
    )
    assert collection is not None
    assert collection.record_type is dict
    assert collection.definition == definition
    assert collection.collection_name == "test-index-name"
    assert collection.search_index_client == search_index_client
    assert collection.search_client == search_client


def test_init_with_search_index_client(azure_ai_search_unit_test_env, definition):
    search_index_client = MagicMock(spec=SearchIndexClient)
    with patch("semantic_kernel.connectors.azure_ai_search._get_search_client") as get_search_client:
        search_client = MagicMock(spec=SearchClient)
        get_search_client.return_value = search_client

        collection = AzureAISearchCollection(
            record_type=dict,
            definition=definition,
            collection_name="test",
            search_index_client=search_index_client,
        )
        assert collection is not None
        assert collection.record_type is dict
        assert collection.definition == definition
        assert collection.collection_name == "test"
        assert collection.search_index_client == search_index_client
        assert collection.search_client == search_client


@mark.parametrize("exclude_list", [["AZURE_AI_SEARCH_INDEX_NAME"]], indirect=True)
def test_init_with_search_index_client_fail(azure_ai_search_unit_test_env, definition):
    search_index_client = MagicMock(spec=SearchIndexClient)
    search_index_client._endpoint = "test-endpoint"
    search_index_client._credential = "test-credential"
    with raises(VectorStoreInitializationException):
        AzureAISearchCollection(
            record_type=dict,
            definition=definition,
            search_index_client=search_index_client,
            env_file_path="test.env",
        )


async def test_upsert(collection, mock_upsert):
    ids = await collection._inner_upsert({"id": "id1", "name": "test"})
    assert ids[0] == "id1"

    ids = await collection.upsert(records={"id": "id1", "content": "content", "vector": [1.0, 2.0, 3.0]})
    assert ids == "id1"


async def test_get(collection, mock_get):
    records = await collection._inner_get(["id1"])
    assert records is not None

    records = await collection.get("id1")
    assert records is not None


@mark.parametrize(
    "order_by, ordering",
    [
        param("id", ["id"], id="single id"),
        param({"id": True}, ["id"], id="ascending id"),
        param({"id": False}, ["id desc"], id="descending id"),
        param(["id"], ["id"], id="ascending id list"),
        param(["id", "content"], ["id", "content"], id="multiple"),
        param([{"id": True}, {"content": False}], ["id", "content desc"], id="multiple desc"),
        param(["id", {"content": False}], ["id", "content desc"], id="multiple mix"),
    ],
)
async def test_get_without_key(collection, mock_get, mock_search, order_by, ordering):
    records = await collection.get(top=10, order_by=order_by)
    assert records is not None
    mock_search.assert_called_once_with(
        search_text="*",
        top=10,
        skip=0,
        select=["id", "content"],
        order_by=ordering,
    )


async def test_delete(collection, mock_delete):
    await collection._inner_delete(["id1"])


async def test_does_collection_exist(collection, mock_list_collection_names):
    await collection.does_collection_exist()


async def test_delete_collection(collection, mock_delete_collection):
    await collection.ensure_collection_deleted()


async def test_create_index_from_index(collection, mock_create_collection):
    from azure.search.documents.indexes.models import SearchIndex

    index = MagicMock(spec=SearchIndex)
    await collection.create_collection(index=index)


async def test_create_index_from_definition(collection, mock_create_collection):
    from azure.search.documents.indexes.models import SearchIndex

    with patch(
        "semantic_kernel.connectors.azure_ai_search._definition_to_azure_ai_search_index",
        return_value=MagicMock(spec=SearchIndex),
    ):
        await collection.create_collection()


async def test_create_index_from_index_fail(collection, mock_create_collection):
    index = Mock()
    with raises(VectorStoreOperationException):
        await collection.create_collection(index=index)


@mark.parametrize("distance_function", [("cosine_distance")])
def test_definition_to_azure_ai_search_index(definition):
    index = _definition_to_azure_ai_search_index("test", definition)
    assert index is not None
    assert index.name == "test"
    assert len(index.fields) == 3


@mark.parametrize("exclude_list", [["AZURE_AI_SEARCH_ENDPOINT"]], indirect=True)
async def test_vector_store_fail(azure_ai_search_unit_test_env):
    with raises(VectorStoreInitializationException):
        AzureAISearchStore(env_file_path="test.env")


async def test_vector_store_list_collection_names(vector_store, mock_list_collection_names):
    assert vector_store.search_index_client is not None
    collection_names = await vector_store.list_collection_names()
    assert collection_names == ["test"]
    mock_list_collection_names.assert_called_once()


async def test_vector_store_does_collection_exists(vector_store, mock_list_collection_names):
    assert vector_store.search_index_client is not None
    exists = await vector_store.does_collection_exist("test")
    assert exists
    mock_list_collection_names.assert_called_once()


async def test_vector_store_delete_collection(vector_store, mock_delete_collection):
    assert vector_store.search_index_client is not None
    await vector_store.ensure_collection_deleted("test")
    mock_delete_collection.assert_called_once()


def test_get_collection(vector_store, definition):
    collection = vector_store.get_collection(
        collection_name="test",
        record_type=dict,
        definition=definition,
    )
    assert collection is not None
    assert collection.collection_name == "test"
    assert collection.search_index_client == vector_store.search_index_client
    assert collection.search_client is not None
    assert collection.search_client._endpoint == vector_store.search_index_client._endpoint


@mark.parametrize("exclude_list", [["AZURE_AI_SEARCH_API_KEY"]], indirect=True)
def test_get_search_index_client(azure_ai_search_unit_test_env):
    from azure.core.credentials import AzureKeyCredential, TokenCredential

    settings = AzureAISearchSettings(**azure_ai_search_unit_test_env, env_file_path="test.env")

    azure_credential = MagicMock(spec=AzureKeyCredential)
    client = _get_search_index_client(settings, azure_credential=azure_credential)
    assert client is not None
    assert client._credential == azure_credential

    token_credential = MagicMock(spec=TokenCredential)
    client2 = _get_search_index_client(
        settings,
        token_credential=token_credential,
    )
    assert client2 is not None
    assert client2._credential == token_credential

    with raises(ServiceInitializationError):
        _get_search_index_client(settings)


@mark.parametrize("include_vectors", [True, False])
async def test_search_vectorized_search(collection, mock_search, include_vectors):
    results = await collection.search(vector=[0.1, 0.2, 0.3], include_vectors=include_vectors)
    assert results is not None
    async for result in results.results:
        assert result is not None
        assert result.record is not None
        assert result.record["id"] == "id1"
        assert result.record["content"] == "content"
        if include_vectors:
            assert result.record["vector"] == [1.0, 2.0, 3.0]
    for call in mock_search.call_args_list:
        assert call[1]["top"] == 3
        assert call[1]["skip"] == 0
        assert call[1]["include_total_count"] is False
        assert call[1]["select"] == ["*"] if include_vectors else ["id", "content"]
        assert call[1]["vector_queries"][0].vector == [0.1, 0.2, 0.3]
        assert call[1]["vector_queries"][0].fields == "vector"


@mark.parametrize("include_vectors", [True, False])
async def test_search_vectorizable_search(collection, mock_search, include_vectors):
    collection.embedding_generator = AsyncMock(spec=EmbeddingGeneratorBase)
    collection.embedding_generator.generate_embeddings.return_value = np.array([[0.1, 0.2, 0.3]])
    results = await collection.search("test", include_vectors=include_vectors)
    assert results is not None
    async for result in results.results:
        assert result is not None
        assert result.record is not None
        assert result.record["id"] == "id1"
        assert result.record["content"] == "content"
        if include_vectors:
            assert result.record["vector"] == [1.0, 2.0, 3.0]
    for call in mock_search.call_args_list:
        assert call[1]["top"] == 3
        assert call[1]["skip"] == 0
        assert call[1]["include_total_count"] is False
        assert call[1]["select"] == ["*"] if include_vectors else ["id", "content"]
        assert call[1]["vector_queries"][0].vector == [0.1, 0.2, 0.3]
        assert call[1]["vector_queries"][0].fields == "vector"


@mark.parametrize("include_vectors", [True, False])
@mark.parametrize("keywords", ["test", ["test1", "test2"]], ids=["single", "multiple"])
async def test_search_keyword_hybrid_search(collection, mock_search, include_vectors, keywords):
    results = await collection.hybrid_search(
        values=keywords,
        vector=[0.1, 0.2, 0.3],
        include_vectors=include_vectors,
        additional_property_name="content",
    )
    assert results is not None
    async for result in results.results:
        assert result is not None
        assert result.record is not None
        assert result.record["id"] == "id1"
        assert result.record["content"] == "content"
        if include_vectors:
            assert result.record["vector"] == [1.0, 2.0, 3.0]
    for call in mock_search.call_args_list:
        assert call[1]["top"] == 3
        assert call[1]["skip"] == 0
        assert call[1]["include_total_count"] is False
        assert call[1]["select"] == ["*"] if include_vectors else ["id", "content"]
        assert call[1]["search_fields"] == ["content"]
        assert call[1]["search_text"] == "test" if keywords == "test" else "test1, test2"
        assert call[1]["vector_queries"][0].vector == [0.1, 0.2, 0.3]
        assert call[1]["vector_queries"][0].fields == "vector"


@mark.parametrize("filter, result", filter_lambda_list("ai_search"))
def test_lambda_filter(collection, filter, result):
    if isinstance(result, type) and issubclass(result, Exception):
        with raises(result):
            collection._build_filter(filter)
    else:
        filter_string = collection._build_filter(filter)
        assert filter_string == result
