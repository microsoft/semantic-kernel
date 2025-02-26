import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from semantic_kernel.connectors.memory.chroma.chroma import ChromaCollection, ChromaStore
from semantic_kernel.data.record_definition.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.record_definition.vector_store_record_fields import VectorStoreRecordKeyField, VectorStoreRecordVectorField, VectorStoreRecordDataField
from semantic_kernel.data.vector_search.vector_search_options import VectorSearchOptions
from semantic_kernel.data.vector_search.vector_search_result import VectorSearchResult
from semantic_kernel.data.kernel_search_results import KernelSearchResults
from semantic_kernel.exceptions.vector_store_exceptions import VectorStoreInitializationException, VectorStoreModelValidationError
from semantic_kernel.memory.memory_record import MemoryRecord
from numpy import array, ndarray

@pytest.fixture
def mock_client():
    return MagicMock()

@pytest.fixture
def mock_collection():
    return MagicMock()

@pytest.fixture
def data_model_definition():
    return VectorStoreRecordDefinition(
        fields={
            "id": VectorStoreRecordKeyField(),
            "content": VectorStoreRecordDataField(
                has_embedding=True,
                embedding_property_name="vector",
            ),
            "vector": VectorStoreRecordVectorField(
                dimensions=5,
                index_kind="hnsw",
                distance_function="cosine_similarity",
                property_type="float",
            ),
        }
    )

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
    assert chroma_collection.data_model_type == dict

def test_chroma_store_initialization(chroma_store):
    assert chroma_store.client is not None

def test_chroma_collection_get_collection(chroma_collection, mock_client):
    mock_client.get_collection.return_value = "mock_collection"
    collection = chroma_collection._get_collection()
    assert collection == "mock_collection"

def test_chroma_store_get_collection(chroma_store, mock_client):
    mock_client.get_collection.return_value = "mock_collection"
    collection = chroma_store.get_collection(
        collection_name="test_collection",
        data_model_type=dict,
    )
    assert collection is not None

async def test_chroma_collection_does_collection_exist(chroma_collection, mock_client):
    mock_client.get_collection.return_value = "mock_collection"
    exists = await chroma_collection.does_collection_exist()
    assert exists

async def test_chroma_store_list_collection_names(chroma_store, mock_client):
    mock_client.list_collections.return_value = [MagicMock(name="collection1"), MagicMock(name="collection2")]
    collections = await chroma_store.list_collection_names()
    assert collections == ["collection1", "collection2"]

async def test_chroma_collection_create_collection(chroma_collection, mock_client):
    await chroma_collection.create_collection()
    mock_client.create_collection.assert_called_once_with(name="test_collection", metadata={})

async def test_chroma_store_create_collection(chroma_store, mock_client):
    await chroma_store.create_collection(collection_name="test_collection", data_model_type=dict)
    mock_client.create_collection.assert_called_once_with(name="test_collection", metadata={})

async def test_chroma_collection_delete_collection(chroma_collection, mock_client):
    await chroma_collection.delete_collection()
    mock_client.delete_collection.assert_called_once_with(name="test_collection")

async def test_chroma_store_delete_collection(chroma_store, mock_client):
    await chroma_store.delete_collection(collection_name="test_collection")
    mock_client.delete_collection.assert_called_once_with(name="test_collection")

async def test_chroma_collection_upsert(chroma_collection, mock_client):
    records = [{"id": "1", "vector": [0.1, 0.2, 0.3, 0.4, 0.5], "document": "test document", "metadata": {}}]
    ids = await chroma_collection._inner_upsert(records)
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
    results = await chroma_collection._inner_search(options, vector=[0.1, 0.2, 0.3, 0.4, 0.5])
    assert len(results.results) == 1
    assert results.results[0].record["id"] == "1"
    assert results.results[0].score == 0.1

def test_chroma_collection_parse_filter(chroma_collection):
    options = VectorSearchOptions(
        top=1,
        include_vectors=True,
        filter=MagicMock(filters=[
            MagicMock(field_name="field1", value="value1", spec=EqualTo),
            MagicMock(field_name="field2", value=["value2", "value3"], spec=AnyTagsEqualTo),
        ])
    )
    filter_expression = chroma_collection._parse_filter(options)
    assert filter_expression == {
        "$and": [
            {"field1": {"$eq": "value1"}},
            {"field2": {"$in": ["value2", "value3"]}},
        ]
    }

def test_chroma_collection_parse_filter_no_filters(chroma_collection):
    options = VectorSearchOptions(
        top=1,
        include_vectors=True,
        filter=MagicMock(filters=[])
    )
    filter_expression = chroma_collection._parse_filter(options)
    assert filter_expression is None

def test_chroma_collection_parse_filter_multiple_filters(chroma_collection):
    options = VectorSearchOptions(
        top=1,
        include_vectors=True,
        filter=MagicMock(filters=[
            MagicMock(field_name="field1", value="value1", spec=EqualTo),
            MagicMock(field_name="field2", value=["value2", "value3"], spec=AnyTagsEqualTo),
            MagicMock(field_name="field3", value="value4", spec=EqualTo),
            MagicMock(field_name="field4", value=["value5", "value6"], spec=AnyTagsEqualTo),
        ])
    )
    filter_expression = chroma_collection._parse_filter(options)
    assert filter_expression == {
        "$and": [
            {"field1": {"$eq": "value1"}},
            {"field2": {"$in": ["value2", "value3"]}},
            {"field3": {"$eq": "value4"}},
            {"field4": {"$in": ["value5", "value6"]}},
        ]
    }
