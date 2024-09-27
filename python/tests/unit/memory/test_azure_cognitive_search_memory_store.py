from unittest.mock import AsyncMock, patch

import pytest
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ResourceNotFoundError
from azure.search.documents.indexes.models import SearchIndex, SearchResourceEncryptionKey

from semantic_kernel.connectors.memory.azure_cognitive_search import AzureCognitiveSearchMemoryStore


@pytest.fixture
def azure_cognitive_search_memory_store():
    """Fixture to instantiate AzureCognitiveSearchMemoryStore with basic configuration."""
    store = AzureCognitiveSearchMemoryStore(
        1536, "https://test.search.windows.net", azure_credentials=AzureKeyCredential("test_key")
    )
    return store


@pytest.fixture
def mock_search_index_client():
    """Fixture to patch 'SearchIndexClient' and its 'create_index' method."""
    with patch("azure.search.documents.indexes.aio.SearchIndexClient.create_index") as mock_create_index:
        # Setup the mock to return a specific SearchIndex instance when called
        mock_create_index.return_value = SearchIndex(name="testIndexWithEncryption", fields=[])
        yield mock_create_index


@pytest.fixture
def mock_encryption_key():
    """Fixture to provide a mock encryption key."""
    return SearchResourceEncryptionKey(
        key_name="mockKeyName", key_version="mockKeyVersion", vault_uri="https://mockvault.vault.azure.net/"
    )


@pytest.fixture
def mock_get_index_client():
    """Fixture to patch 'SearchIndexClient.get_index' method to raise ResourceNotFoundError."""
    with patch("azure.search.documents.indexes.aio.SearchIndexClient.get_index", new_callable=AsyncMock) as mock:
        mock.side_effect = ResourceNotFoundError("The specified index was not found.")
        yield mock


@pytest.mark.asyncio
async def test_create_collection_without_encryption_key(
    azure_cognitive_search_memory_store, mock_search_index_client, mock_get_index_client
):
    mock_search_index_client.return_value = SearchIndex(name="testIndex", fields=[])
    await azure_cognitive_search_memory_store.create_collection("testIndex")

    mock_search_index_client.assert_called_once()
    args, kwargs = mock_search_index_client.call_args
    created_index: SearchIndex = args[0]

    assert created_index.encryption_key is None, "Encryption key should be None"


@pytest.mark.asyncio
async def test_create_collection_with_encryption_key(
    azure_cognitive_search_memory_store, mock_search_index_client, mock_encryption_key, mock_get_index_client
):
    mock_search_index_client.return_value = SearchIndex(
        name="testIndexWithEncryption", fields=[], search_resource_encryption_key=mock_encryption_key
    )
    await azure_cognitive_search_memory_store.create_collection(
        "testIndexWithEncryption", search_resource_encryption_key=mock_encryption_key
    )

    mock_search_index_client.assert_called_once()
    args, kwargs = mock_search_index_client.call_args
    created_index: SearchIndex = args[0]

    assert created_index.encryption_key == mock_encryption_key, "Encryption key was not set correctly"
