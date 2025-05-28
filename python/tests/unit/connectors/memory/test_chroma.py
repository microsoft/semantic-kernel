# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import MagicMock

import pytest
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection

from semantic_kernel.connectors.chroma import ChromaCollection, ChromaStore


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


async def test_chroma_collection_does_collection_exist(chroma_collection, mock_client):
    mock_client.get_collection.return_value = "mock_collection"
    exists = await chroma_collection.does_collection_exist()
    assert exists


async def test_chroma_store_list_collection_names(chroma_store, mock_client):
    mock_collection = MagicMock(spec=Collection)
    mock_collection.name = "test_collection"
    mock_client.list_collections.return_value = [mock_collection]
    collections = await chroma_store.list_collection_names()
    assert collections == ["test_collection"]


async def test_chroma_collection_create_collection(chroma_collection, mock_client):
    await chroma_collection.create_collection()
    mock_client.create_collection.assert_called_once_with(
        name="test_collection", embedding_function=None, configuration={"hnsw": {"space": "cosine"}}, get_or_create=True
    )


async def test_chroma_collection_delete_collection(chroma_collection, mock_client):
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
