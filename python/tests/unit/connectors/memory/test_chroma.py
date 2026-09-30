# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import MagicMock

import pytest
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection

from semantic_kernel.connectors.chroma import ChromaCollection, ChromaStore
from semantic_kernel.exceptions.vector_store_exceptions import VectorStoreOperationException

try:  # mirrors the connector, resolved here so these tests do not depend on it
    from chromadb.errors import NotFoundError as _ChromaNotFoundError

    COLLECTION_NOT_FOUND_IS_VALUE_ERROR = False
except ImportError:  # chromadb < 1.0
    _ChromaNotFoundError = ValueError
    COLLECTION_NOT_FOUND_IS_VALUE_ERROR = True


def _not_found() -> Exception:
    """The error Chroma raises for a missing collection, on whichever version is installed.

    Resolved here rather than imported from the connector, so these tests run unchanged
    against the code before and after the fix.
    """
    return _ChromaNotFoundError("Collection test_collection does not exist.")


@pytest.fixture
def mock_client():
    return MagicMock(spec=ClientAPI)


@pytest.fixture
def chroma_collection(mock_client, definition):
    return ChromaCollection(
        collection_name="test_collection",
        record_type=dict,
        definition=definition,
        client=mock_client,
    )


@pytest.fixture
def chroma_store(mock_client):
    return ChromaStore(client=mock_client)


def test_chroma_collection_initialization(chroma_collection):
    assert chroma_collection.collection_name == "test_collection"
    assert chroma_collection.record_type is dict


def test_chroma_store_initialization(chroma_store):
    assert chroma_store.client is not None


def test_chroma_collection_get_collection(chroma_collection, mock_client):
    mock_client.get_collection.return_value = "mock_collection"
    collection = chroma_collection._get_collection()
    assert collection == "mock_collection"


def test_chroma_store_get_collection(chroma_store, mock_client, definition):
    collection = chroma_store.get_collection(collection_name="test_collection", record_type=dict, definition=definition)
    assert collection is not None
    assert isinstance(collection, ChromaCollection)


async def test_chroma_collection_collection_exists(chroma_collection, mock_client):
    mock_client.get_collection.return_value = "mock_collection"
    exists = await chroma_collection.collection_exists()
    assert exists


async def test_chroma_store_list_collection_names(chroma_store, mock_client):
    mock_collection = MagicMock(spec=Collection)
    mock_collection.name = "test_collection"
    mock_client.list_collections.return_value = [mock_collection]
    collections = await chroma_store.list_collection_names()
    assert collections == ["test_collection"]


async def test_chroma_collection_ensure_collection_exists(chroma_collection, mock_client):
    await chroma_collection.ensure_collection_exists()
    mock_client.create_collection.assert_called_once_with(
        name="test_collection", embedding_function=None, configuration={"hnsw": {"space": "cosine"}}, get_or_create=True
    )


async def test_chroma_collection_ensure_collection_deleted(chroma_collection, mock_client):
    await chroma_collection.ensure_collection_deleted()
    mock_client.delete_collection.assert_called_once_with(name="test_collection")


async def test_chroma_collection_upsert(chroma_collection, mock_client):
    records = [{"id": "1", "vector": [0.1, 0.2, 0.3, 0.4, 0.5], "content": "test document"}]
    ids = await chroma_collection.upsert(records)
    assert ids == ["1"]
    mock_client.get_collection().add.assert_called_once()


async def test_chroma_collection_get(chroma_collection, mock_client):
    mock_client.get_collection().get.return_value = {
        "ids": [["1"]],
        "documents": [["test document"]],
        "embeddings": [[[0.1, 0.2, 0.3, 0.4, 0.5]]],
        "metadatas": [[{}]],
    }
    records = await chroma_collection._inner_get(["1"])
    assert len(records) == 1
    assert records[0]["id"] == "1"


async def test_chroma_collection_delete(chroma_collection, mock_client):
    await chroma_collection._inner_delete(["1"])
    mock_client.get_collection().delete.assert_called_once_with(ids=["1"])


@pytest.mark.parametrize("include_vectors", [True, False])
async def test_chroma_collection_search(chroma_collection, mock_client, include_vectors):
    mock_client.get_collection().query.return_value = {
        "ids": [["1"]],
        "documents": [["test document"]],
        "embeddings": [[[0.1, 0.2, 0.3, 0.4, 0.5]]],
        "metadatas": [[{}]],
        "distances": [[0.1]],
    }
    results = await chroma_collection.search(vector=[0.1, 0.2, 0.3, 0.4, 0.5], top=1, include_vectors=include_vectors)
    async for res in results.results:
        assert res.record["id"] == "1"
        assert res.score == 0.1


# -- what a Chroma failure means, and what "not there" means --
#
# chromadb changed the error for a missing collection inside the supported range
# (chromadb >= 0.5, < 1.6): 0.5 raised ValueError, 1.0 raises errors.NotFoundError,
# which is not a ValueError. collection_exists caught bare Exception, so every failure
# read as "absent"; ensure_collection_deleted caught only ValueError, so on a modern
# chromadb a genuinely absent collection raised instead of being tolerated.


async def test_collection_exists_is_false_when_chroma_says_not_found(chroma_collection, mock_client):
    mock_client.get_collection.side_effect = _not_found()

    assert await chroma_collection.collection_exists() is False


async def test_collection_exists_raises_when_the_server_cannot_be_reached(chroma_collection, mock_client):
    """False means the collection is not there. A refused connection must not say that."""
    mock_client.get_collection.side_effect = ConnectionError("connection refused")

    with pytest.raises(ConnectionError):
        await chroma_collection.collection_exists()


async def test_ensure_collection_deleted_tolerates_an_absent_collection(chroma_collection, mock_client):
    """Deleting something that is not there is the case this method already meant to allow."""
    mock_client.delete_collection.side_effect = _not_found()

    await chroma_collection.ensure_collection_deleted()


async def test_ensure_collection_deleted_still_raises_on_a_real_failure(chroma_collection, mock_client):
    mock_client.delete_collection.side_effect = ConnectionError("connection refused")

    with pytest.raises(VectorStoreOperationException):
        await chroma_collection.ensure_collection_deleted()


@pytest.mark.skipif(
    COLLECTION_NOT_FOUND_IS_VALUE_ERROR,
    reason="on chromadb < 1.0 a ValueError IS the missing-collection signal",
)
async def test_collection_exists_raises_on_an_unrelated_value_error(chroma_collection, mock_client):
    """Where Chroma has a dedicated NotFoundError, a ValueError is not 'absent'."""
    mock_client.get_collection.side_effect = ValueError("some other problem")

    with pytest.raises(ValueError):
        await chroma_collection.collection_exists()


@pytest.mark.skipif(
    COLLECTION_NOT_FOUND_IS_VALUE_ERROR,
    reason="on chromadb < 1.0 a ValueError IS the missing-collection signal",
)
async def test_ensure_collection_deleted_does_not_swallow_an_unrelated_value_error(chroma_collection, mock_client):
    """The more dangerous half: a swallowed ValueError here would silently skip a delete."""
    mock_client.delete_collection.side_effect = ValueError("some other problem")

    with pytest.raises(VectorStoreOperationException):
        await chroma_collection.ensure_collection_deleted()
