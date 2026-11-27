# Copyright (c) Microsoft. All rights reserved.

import uuid
from dataclasses import dataclass
from unittest.mock import MagicMock

import chromadb
import pytest
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection
from chromadb.errors import NotFoundError
from pydantic import BaseModel

from semantic_kernel.connectors.chroma import ChromaCollection, ChromaStore
from semantic_kernel.data.vector import VectorStoreCollectionDefinition, VectorStoreField
from semantic_kernel.exceptions.vector_store_exceptions import VectorStoreOperationException


def _not_found() -> Exception:
    """The error Chroma raises for a missing collection."""
    return NotFoundError("Collection test_collection does not exist.")


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
# chromadb 1.x raises errors.NotFoundError for a missing collection, which is not a
# ValueError (this connector only imports on chromadb 1.x: it needs
# chromadb.api.collection_configuration). collection_exists caught bare Exception, so every failure
# read as "absent"; ensure_collection_deleted caught only ValueError, so on a modern
# chromadb a genuinely absent collection raised instead of being tolerated.


async def test_collection_exists_is_false_when_chroma_says_not_found(chroma_collection, mock_client):
    mock_client.get_collection.side_effect = _not_found()

    assert await chroma_collection.collection_exists() is False


async def test_collection_exists_raises_when_the_server_cannot_be_reached(chroma_collection, mock_client):
    """False means the collection is not there. A refused connection must not say that."""
    mock_client.get_collection.side_effect = ConnectionError("connection refused")

    with pytest.raises(VectorStoreOperationException) as raised:
        await chroma_collection.collection_exists()
    assert isinstance(raised.value.__cause__, ConnectionError)


async def test_ensure_collection_deleted_tolerates_an_absent_collection(chroma_collection, mock_client):
    """Deleting something that is not there is the case this method already meant to allow."""
    mock_client.delete_collection.side_effect = _not_found()

    await chroma_collection.ensure_collection_deleted()


async def test_ensure_collection_deleted_still_raises_on_a_real_failure(chroma_collection, mock_client):
    mock_client.delete_collection.side_effect = ConnectionError("connection refused")

    with pytest.raises(VectorStoreOperationException):
        await chroma_collection.ensure_collection_deleted()


async def test_collection_exists_raises_on_an_unrelated_value_error(chroma_collection, mock_client):
    """Where Chroma has a dedicated NotFoundError, a ValueError is not 'absent'."""
    mock_client.get_collection.side_effect = ValueError("some other problem")

    with pytest.raises(VectorStoreOperationException):
        await chroma_collection.collection_exists()


async def test_ensure_collection_deleted_does_not_swallow_an_unrelated_value_error(chroma_collection, mock_client):
    """The more dangerous half: a swallowed ValueError here would silently skip a delete."""
    mock_client.delete_collection.side_effect = ValueError("some other problem")

    with pytest.raises(VectorStoreOperationException):
        await chroma_collection.ensure_collection_deleted()


def test_chroma_collection_build_filter_keeps_apostrophes(chroma_collection):
    """Chroma filters are dicts, not SQL, so the value must reach Chroma unchanged."""
    assert chroma_collection._build_filter('lambda x: x.content == "O\'Brien"') == {"content": "O'Brien"}
    assert chroma_collection._build_filter('lambda x: x.content != "O\'Brien"') == {"content": {"$ne": "O'Brien"}}


@dataclass
class AliasedDataclass:
    id: str
    text: str
    vector: list[float] | None = None


class AliasedModel(BaseModel):
    id: str
    text: str
    vector: list[float] | None = None


@pytest.mark.parametrize("key_storage_name", [None, "point_id"], ids=["plain_key", "aliased_key"])
@pytest.mark.parametrize("record_type", [dict, AliasedDataclass, AliasedModel])
async def test_storage_names_round_trip(record_type, key_storage_name):
    definition = VectorStoreCollectionDefinition(
        fields=[
            VectorStoreField("key", name="id", type="str", storage_name=key_storage_name),
            VectorStoreField("data", name="text", type="str", storage_name="doc_text", is_indexed=True),
            VectorStoreField("vector", name="vector", dimensions=2, type="float", storage_name="doc_vector"),
        ]
    )

    def make(record_id: str, text: str, vector: list[float]):
        values = {"id": record_id, "text": text, "vector": vector}
        return values if record_type is dict else record_type(**values)

    def as_dict(record):
        if isinstance(record, dict):
            values = dict(record)
        else:
            values = dict(vars(record)) if record_type is AliasedDataclass else record.model_dump()
        if values.get("vector") is not None:
            values["vector"] = [float(x) for x in values["vector"]]
        return values

    collection = ChromaCollection(
        record_type=record_type,
        definition=definition,
        collection_name=f"test-{uuid.uuid4().hex}",
        client=chromadb.EphemeralClient(),
    )
    await collection.ensure_collection_exists()
    try:
        await collection.upsert([make("k1", "a", [1.0, 0.0]), make("k2", "b", [0.0, 1.0])])

        stored = as_dict(await collection.get("k1", include_vectors=True))
        assert stored == {"id": "k1", "text": "a", "vector": [1.0, 0.0]}

        results = await collection.search(vector=[0.0, 1.0], include_vectors=True)
        found = [as_dict(r.record) async for r in results.results]
        assert [r["id"] for r in found] == ["k2", "k1"]
        assert found[0] == {"id": "k2", "text": "b", "vector": [0.0, 1.0]}

        # filters use the storage names, so the metadata must be stored under them for every record type
        results = await collection.search(vector=[0.0, 1.0], filter="lambda x: x.doc_text == 'a'")
        assert [as_dict(r.record)["id"] async for r in results.results] == ["k1"]
    finally:
        await collection.ensure_collection_deleted()
