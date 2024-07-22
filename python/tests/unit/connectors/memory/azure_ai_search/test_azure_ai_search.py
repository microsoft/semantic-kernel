# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import MagicMock, patch

from pytest import fixture, mark, raises

from semantic_kernel.connectors.memory.azure_ai_search.azure_ai_search_settings import AzureAISearchSettings
from semantic_kernel.connectors.memory.azure_ai_search.azure_ai_search_store import AzureAISearchStore
from semantic_kernel.connectors.memory.azure_ai_search.utils import get_search_index_client
from semantic_kernel.exceptions.memory_connector_exceptions import MemoryConnectorInitializationError
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError


class AsyncIter:
    def __init__(self, items):
        self.items = items

    async def __aiter__(self):
        for item in self.items:
            yield item


@fixture
def vector_store(azure_ai_search_unit_test_env):
    """Fixture to instantiate AzureCognitiveSearchMemoryStore with basic configuration."""
    return AzureAISearchStore()


@fixture
def mock_list_index_client():
    """Fixture to patch 'SearchIndexClient' and its 'create_index' method."""
    with patch("azure.search.documents.indexes.aio.SearchIndexClient.list_index_names") as mock_list_index_names:
        # Setup the mock to return a specific SearchIndex instance when called
        mock_list_index_names.return_value = AsyncIter(["test"])
        yield mock_list_index_names


@mark.asyncio
@mark.parametrize("exclude_list", [["AZURE_AI_SEARCH_ENDPOINT"]], indirect=True)
async def test_vector_store_fail(azure_ai_search_unit_test_env):
    with raises(MemoryConnectorInitializationError):
        AzureAISearchStore(env_file_path="test.env")


@mark.asyncio
async def test_vector_store_list_collection_names(vector_store, mock_list_index_client):
    assert vector_store.search_index_client is not None
    collection_names = await vector_store.list_collection_names()
    assert collection_names == ["test"]
    mock_list_index_client.assert_called_once()


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

    settings = AzureAISearchSettings.create(**azure_ai_search_unit_test_env, env_file_path="test.env")

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
