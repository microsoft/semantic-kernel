# Copyright (c) Microsoft. All rights reserved.


from unittest.mock import MagicMock, Mock, patch

from pytest import fixture, mark, raises

from semantic_kernel.connectors.memory.azure_ai_search.azure_ai_search_collection import AzureAISearchCollection
from semantic_kernel.connectors.memory.azure_ai_search.azure_ai_search_settings import AzureAISearchSettings
from semantic_kernel.connectors.memory.azure_ai_search.azure_ai_search_store import AzureAISearchStore
from semantic_kernel.connectors.memory.azure_ai_search.utils import (
    SearchClientWrapper,
    SearchIndexClientWrapper,
    data_model_definition_to_azure_ai_search_index,
    get_search_index_client,
)
from semantic_kernel.exceptions import (
    ServiceInitializationError,
    VectorStoreInitializationException,
    VectorStoreOperationException,
)
from semantic_kernel.utils.list_handler import desync_list

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
def mock_delete():
    with patch(f"{BASE_PATH_SEARCH_CLIENT}.delete_documents") as mock_delete_documents:
        yield mock_delete_documents


@fixture
def collection(azure_ai_search_unit_test_env, data_model_definition):
    return AzureAISearchCollection(data_model_type=dict, data_model_definition=data_model_definition)


def test_init(azure_ai_search_unit_test_env, data_model_definition):
    collection = AzureAISearchCollection(data_model_type=dict, data_model_definition=data_model_definition)
    assert collection is not None
    assert collection.data_model_type is dict
    assert collection.data_model_definition == data_model_definition
    assert collection.collection_name == "test-index-name"
    assert collection.search_index_client is not None
    assert collection.search_client is not None


def test_init_with_type(azure_ai_search_unit_test_env, data_model_type):
    collection = AzureAISearchCollection(data_model_type=data_model_type)
    assert collection is not None
    assert collection.data_model_type is data_model_type
    assert collection.collection_name == "test-index-name"
    assert collection.search_index_client is not None
    assert collection.search_client is not None


@mark.parametrize("exclude_list", [["AZURE_AI_SEARCH_ENDPOINT"]], indirect=True)
def test_init_endpoint_fail(azure_ai_search_unit_test_env, data_model_definition):
    with raises(VectorStoreInitializationException):
        AzureAISearchCollection(
            data_model_type=dict, data_model_definition=data_model_definition, env_file_path="test.env"
        )


@mark.parametrize("exclude_list", [["AZURE_AI_SEARCH_INDEX_NAME"]], indirect=True)
def test_init_index_fail(azure_ai_search_unit_test_env, data_model_definition):
    with raises(VectorStoreInitializationException):
        AzureAISearchCollection(
            data_model_type=dict, data_model_definition=data_model_definition, env_file_path="test.env"
        )


def test_init_with_clients(azure_ai_search_unit_test_env, data_model_definition):
    search_index_client = MagicMock(spec=SearchIndexClientWrapper)
    search_client = MagicMock(spec=SearchClientWrapper)
    search_client._index_name = "test-index-name"

    collection = AzureAISearchCollection(
        data_model_type=dict,
        data_model_definition=data_model_definition,
        search_index_client=search_index_client,
        search_client=search_client,
    )
    assert collection is not None
    assert collection.data_model_type is dict
    assert collection.data_model_definition == data_model_definition
    assert collection.collection_name == "test-index-name"
    assert collection.search_index_client == search_index_client
    assert collection.search_client == search_client


def test_init_with_search_index_client(azure_ai_search_unit_test_env, data_model_definition):
    search_index_client = MagicMock(spec=SearchIndexClientWrapper)
    with patch(
        "semantic_kernel.connectors.memory.azure_ai_search.azure_ai_search_collection.get_search_client"
    ) as get_search_client:
        search_client = MagicMock(spec=SearchClientWrapper)
        get_search_client.return_value = search_client

        collection = AzureAISearchCollection(
            data_model_type=dict,
            data_model_definition=data_model_definition,
            collection_name="test",
            search_index_client=search_index_client,
        )
        assert collection is not None
        assert collection.data_model_type is dict
        assert collection.data_model_definition == data_model_definition
        assert collection.collection_name == "test"
        assert collection.search_index_client == search_index_client
        assert collection.search_client == search_client


def test_init_with_search_index_client_fail(azure_ai_search_unit_test_env, data_model_definition):
    search_index_client = MagicMock(spec=SearchIndexClientWrapper)
    with raises(VectorStoreInitializationException, match="Collection name is required."):
        AzureAISearchCollection(
            data_model_type=dict,
            data_model_definition=data_model_definition,
            search_index_client=search_index_client,
        )


def test_init_with_clients_fail(azure_ai_search_unit_test_env, data_model_definition):
    search_index_client = MagicMock(spec=SearchIndexClientWrapper)
    search_client = MagicMock(spec=SearchClientWrapper)
    search_client._index_name = "test-index-name"

    with raises(
        VectorStoreInitializationException, match="Search client and search index client have different index names."
    ):
        AzureAISearchCollection(
            data_model_type=dict,
            data_model_definition=data_model_definition,
            collection_name="test",
            search_index_client=search_index_client,
            search_client=search_client,
        )


async def test_upsert(collection, mock_upsert):
    ids = await collection._inner_upsert({"id": "id1", "name": "test"})
    assert ids[0] == "id1"

    ids = await collection.upsert(record={"id": "id1", "content": "content", "vector": [1.0, 2.0, 3.0]})
    assert ids == "id1"


async def test_get(collection, mock_get):
    records = await collection._inner_get(["id1"])
    assert records is not None

    records = await collection.get("id1")
    assert records is not None


async def test_delete(collection, mock_delete):
    await collection._inner_delete(["id1"])


async def test_does_collection_exist(collection, mock_list_collection_names):
    await collection.does_collection_exist()


async def test_delete_collection(collection, mock_delete_collection):
    await collection.delete_collection()


async def test_create_index_from_index(collection, mock_create_collection):
    from azure.search.documents.indexes.models import SearchIndex

    index = MagicMock(spec=SearchIndex)
    await collection.create_collection(index=index)


async def test_create_index_from_definition(collection, mock_create_collection):
    from azure.search.documents.indexes.models import SearchIndex

    with patch(
        "semantic_kernel.connectors.memory.azure_ai_search.azure_ai_search_collection.data_model_definition_to_azure_ai_search_index",
        return_value=MagicMock(spec=SearchIndex),
    ):
        await collection.create_collection()


async def test_create_index_from_index_fail(collection, mock_create_collection):
    index = Mock()
    with raises(VectorStoreOperationException):
        await collection.create_collection(index=index)


@mark.parametrize("distance_function", [("cosine_distance")])
def test_data_model_definition_to_azure_ai_search_index(data_model_definition):
    index = data_model_definition_to_azure_ai_search_index("test", data_model_definition)
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


def test_get_collection(vector_store, data_model_definition):
    collection = vector_store.get_collection(
        collection_name="test",
        data_model_type=dict,
        data_model_definition=data_model_definition,
    )
    assert collection is not None
    assert collection.collection_name == "test"
    assert collection.search_index_client == vector_store.search_index_client
    assert collection.search_client is not None
    assert collection.search_client._endpoint == vector_store.search_index_client._endpoint
    assert vector_store.vector_record_collections["test"] == collection


@mark.parametrize("exclude_list", [["AZURE_AI_SEARCH_API_KEY"]], indirect=True)
def test_get_search_index_client(azure_ai_search_unit_test_env):
    from azure.core.credentials import AzureKeyCredential, TokenCredential

    settings = AzureAISearchSettings(**azure_ai_search_unit_test_env, env_file_path="test.env")

    azure_credential = MagicMock(spec=AzureKeyCredential)
    client = get_search_index_client(settings, azure_credential=azure_credential)
    assert client is not None
    assert client._credential == azure_credential

    token_credential = MagicMock(spec=TokenCredential)
    client2 = get_search_index_client(
        settings,
        token_credential=token_credential,
    )
    assert client2 is not None
    assert client2._credential == token_credential

    with raises(ServiceInitializationError):
        get_search_index_client(settings)
