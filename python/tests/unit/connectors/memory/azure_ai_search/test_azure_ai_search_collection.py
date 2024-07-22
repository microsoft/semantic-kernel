# Copyright (c) Microsoft. All rights reserved.


from unittest.mock import MagicMock

from pytest import fixture

from semantic_kernel.connectors.memory.azure_ai_search.azure_ai_search_collection import AzureAISearchCollection
from semantic_kernel.connectors.memory.azure_ai_search.azure_ai_search_store import AzureAISearchStore
from semantic_kernel.connectors.memory.azure_ai_search.utils import SearchClientWrapper, SearchIndexClientWrapper


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


# @fixture
# def mock_list_index_client():
#     """Fixture to patch 'SearchIndexClient' and its 'create_index' method."""
#     with patch("azure.search.documents.indexes.aio.SearchIndexClient.list_index_names") as mock_list_index_names:
#         # Setup the mock to return a specific SearchIndex instance when called
#         mock_list_index_names.return_value = AsyncIter(["test"])
#         yield mock_list_index_name


def test_init(azure_ai_search_unit_test_env, data_model_definition):
    collection = AzureAISearchCollection(data_model_type=dict, data_model_definition=data_model_definition)
    assert collection is not None
    assert collection.data_model_type is dict
    assert collection.data_model_definition == data_model_definition
    assert collection.collection_name == "test-index-name"
    assert collection.search_index_client is not None
    assert collection.search_client is not None


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
