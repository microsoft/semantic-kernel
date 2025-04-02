# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import MagicMock

import pytest
from chromadb.api import ClientAPI

from semantic_kernel.connectors.memory.chroma.chroma import ChromaCollection, ChromaStore
from semantic_kernel.data.vector_search import VectorSearchFilter, VectorSearchOptions


@pytest.fixture
def mock_client():
    return MagicMock(spec=ClientAPI)


@pytest.fixture
def chroma_collection(mock_client, data_model_definition):
    return ChromaCollection(
        collection_name="test_collection",
        data_model_type=dict,
        data_model_definition=data_model_definition,
        client=mock_client,
    )


@pytest.fixture
def chroma_store(mock_client):
    return ChromaStore(client=mock_client)


def test_chroma_collection_initialization(chroma_collection):
    assert chroma_collection.collection_name == "test_collection"
    assert chroma_collection.data_model_type is dict


def test_chroma_store_initialization(chroma_store):
    assert chroma_store.client is not None


def test_chroma_collection_get_collection(chroma_collection, mock_client):
    mock_client.get_collection.return_value = "mock_collection"
    collection = chroma_collection._get_collection()
    assert collection == "mock_collection"


def test_chroma_store_get_collection(chroma_store, mock_client, data_model_definition):
    collection = chroma_store.get_collection(
        collection_name="test_collection", data_model_type=dict, data_model_definition=data_model_definition
    )
    assert collection is not None
    assert isinstance(collection, ChromaCollection)


async def test_chroma_collection_does_collection_exist(chroma_collection, mock_client):
    mock_client.get_collection.return_value = "mock_collection"
    exists = await chroma_collection.does_collection_exist()
    assert exists


async def test_chroma_store_list_collection_names(chroma_store, mock_client):
    mock_client.list_collections.return_value = ["collection1", "collection2"]
    collections = await chroma_store.list_collection_names()
    assert collections == ["collection1", "collection2"]


async def test_chroma_collection_create_collection(chroma_collection, mock_client):
    await chroma_collection.create_collection()
    mock_client.create_collection.assert_called_once_with(name="test_collection", metadata={"hnsw:space": "cosine"})


async def test_chroma_collection_delete_collection(chroma_collection, mock_client):
    await chroma_collection.delete_collection()
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


async def test_chroma_collection_search(chroma_collection, mock_client):
    options = VectorSearchOptions(top=1, include_vectors=True)
    mock_client.get_collection().query.return_value = {
        "ids": [["1"]],
        "documents": [["test document"]],
        "embeddings": [[[0.1, 0.2, 0.3, 0.4, 0.5]]],
        "metadatas": [[{}]],
        "distances": [[0.1]],
    }
    results = await chroma_collection.vectorized_search(options=options, vector=[0.1, 0.2, 0.3, 0.4, 0.5])
    async for res in results.results:
        assert res.record["id"] == "1"
        assert res.score == 0.1


@pytest.mark.parametrize(
    "filter_expression, expected",
    [
        pytest.param(
            VectorSearchFilter.equal_to("field1", "value1"), {"field1": {"$eq": "value1"}}, id="single_filter"
        ),
        pytest.param(VectorSearchFilter(), None, id="empty_filter"),
        pytest.param(
            VectorSearchFilter.equal_to("field1", "value1").any_tag_equal_to("field2", ["value2", "value3"]),
            {"$and": [{"field1": {"$eq": "value1"}}, {"field2": {"$in": ["value2", "value3"]}}]},
            id="multiple_filters",
        ),
    ],
)
def test_chroma_collection_parse_filter(chroma_collection, filter_expression, expected):
    options = VectorSearchOptions(top=1, include_vectors=True, filter=filter_expression)
    filter_expression = chroma_collection._parse_filter(options)
    assert filter_expression == expected
