# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import MagicMock, patch

from pytest import fixture, mark, raises
from qdrant_client.async_qdrant_client import AsyncQdrantClient
from qdrant_client.models import Datatype, Distance, VectorParams

from semantic_kernel.connectors.memory.qdrant.qdrant_collection import QdrantCollection
from semantic_kernel.connectors.memory.qdrant.qdrant_store import QdrantStore
from semantic_kernel.data.vector_store_record_fields import VectorStoreRecordVectorField
from semantic_kernel.exceptions.memory_connector_exceptions import (
    MemoryConnectorException,
    MemoryConnectorInitializationError,
    VectorStoreModelValidationError,
)

BASE_PATH = "qdrant_client.async_qdrant_client.AsyncQdrantClient"


@fixture
def vector_store(qdrant_unit_test_env):
    return QdrantStore(env_file_path="test.env")


@fixture
def collection(qdrant_unit_test_env, data_model_definition):
    return QdrantCollection(
        data_model_type=dict,
        collection_name="test",
        data_model_definition=data_model_definition,
        env_file_path="test.env",
    )


@fixture
def collection_without_named_vectors(qdrant_unit_test_env, data_model_definition):
    return QdrantCollection(
        data_model_type=dict,
        collection_name="test",
        data_model_definition=data_model_definition,
        named_vectors=False,
        env_file_path="test.env",
    )


@fixture(autouse=True)
def mock_list_collection_names():
    with patch(f"{BASE_PATH}.get_collections") as mock_get_collections:
        from qdrant_client.conversions.common_types import CollectionsResponse
        from qdrant_client.http.models import CollectionDescription

        response = MagicMock(spec=CollectionsResponse)
        response.collections = [CollectionDescription(name="test")]
        mock_get_collections.return_value = response
        yield mock_get_collections


@fixture(autouse=True)
def mock_does_collection_exist():
    with patch(f"{BASE_PATH}.collection_exists") as mock_collection_exists:
        mock_collection_exists.return_value = True
        yield mock_collection_exists


@fixture(autouse=True)
def mock_create_collection():
    with patch(f"{BASE_PATH}.create_collection") as mock_recreate_collection:
        yield mock_recreate_collection


@fixture(autouse=True)
def mock_delete_collection():
    with patch(f"{BASE_PATH}.delete_collection") as mock_delete_collection:
        mock_delete_collection.return_value = True
        yield mock_delete_collection


@fixture(autouse=True)
def mock_upsert():
    with patch(f"{BASE_PATH}.upsert") as mock_upsert:
        from qdrant_client.conversions.common_types import UpdateResult

        result = MagicMock(spec=UpdateResult)
        result.status = "completed"
        mock_upsert.return_value = result
        yield mock_upsert


@fixture(autouse=True)
def mock_get(collection):
    with patch(f"{BASE_PATH}.retrieve") as mock_retrieve:
        from qdrant_client.http.models import Record

        if collection.named_vectors:
            mock_retrieve.return_value = [
                Record(id="id1", payload={"content": "content"}, vector={"vector": [1.0, 2.0, 3.0]})
            ]
        else:
            mock_retrieve.return_value = [Record(id="id1", payload={"content": "content"}, vector=[1.0, 2.0, 3.0])]
        yield mock_retrieve


@fixture(autouse=True)
def mock_delete():
    with patch(f"{BASE_PATH}.delete") as mock_delete:
        yield mock_delete


def test_vector_store_defaults(vector_store):
    assert vector_store.qdrant_client is not None
    assert vector_store.qdrant_client._client.rest_uri == "http://localhost:6333"


def test_vector_store_with_client():
    qdrant_store = QdrantStore(client=AsyncQdrantClient())
    assert qdrant_store.qdrant_client is not None
    assert qdrant_store.qdrant_client._client.rest_uri == "http://localhost:6333"


@mark.parametrize("exclude_list", [["QDRANT_LOCATION"]], indirect=True)
def test_vector_store_in_memory(qdrant_unit_test_env):
    from qdrant_client.local.async_qdrant_local import AsyncQdrantLocal

    qdrant_store = QdrantStore(api_key="supersecretkey", env_file_path="test.env")
    assert qdrant_store.qdrant_client is not None
    assert isinstance(qdrant_store.qdrant_client._client, AsyncQdrantLocal)
    assert qdrant_store.qdrant_client._client.location == ":memory:"


def test_vector_store_fail():
    with raises(MemoryConnectorInitializationError, match="Failed to create Qdrant settings."):
        QdrantStore(location="localhost", url="localhost", env_file_path="test.env")

    with raises(MemoryConnectorInitializationError, match="Failed to create Qdrant client."):
        QdrantStore(location="localhost", url="http://localhost", env_file_path="test.env")


@mark.asyncio
async def test_store_list_collection_names(vector_store):
    collections = await vector_store.list_collection_names()
    assert collections == ["test"]


def test_get_collection(vector_store, data_model_definition, qdrant_unit_test_env):
    collection = vector_store.get_collection("test", data_model_type=dict, data_model_definition=data_model_definition)
    assert collection.collection_name == "test"
    assert collection.qdrant_client == vector_store.qdrant_client
    assert collection.data_model_type is dict
    assert collection.data_model_definition == data_model_definition
    assert vector_store.vector_record_collections["test"] == collection


def test_collection_init(data_model_definition, qdrant_unit_test_env):
    collection = QdrantCollection(
        data_model_type=dict,
        collection_name="test",
        data_model_definition=data_model_definition,
        env_file_path="test.env",
    )
    assert collection.collection_name == "test"
    assert collection.qdrant_client is not None
    assert collection.data_model_type is dict
    assert collection.data_model_definition == data_model_definition
    assert collection.named_vectors


def test_collection_init_fail(data_model_definition):
    with raises(MemoryConnectorInitializationError, match="Failed to create Qdrant settings."):
        QdrantCollection(
            data_model_type=dict,
            collection_name="test",
            data_model_definition=data_model_definition,
            url="localhost",
            env_file_path="test.env",
        )
    with raises(MemoryConnectorInitializationError, match="Failed to create Qdrant client."):
        QdrantCollection(
            data_model_type=dict,
            collection_name="test",
            data_model_definition=data_model_definition,
            location="localhost",
            url="http://localhost",
            env_file_path="test.env",
        )
    with raises(
        VectorStoreModelValidationError, match="Only one vector field is allowed when not using named vectors."
    ):
        data_model_definition.fields["vector2"] = VectorStoreRecordVectorField(name="vector2", dimensions=3)
        QdrantCollection(
            data_model_type=dict,
            collection_name="test",
            data_model_definition=data_model_definition,
            named_vectors=False,
            env_file_path="test.env",
        )


@mark.asyncio
@mark.parametrize("collection_to_use", ["collection", "collection_without_named_vectors"])
async def test_upsert(collection_to_use, request):
    from qdrant_client.models import PointStruct

    collection = request.getfixturevalue(collection_to_use)
    if collection.named_vectors:
        record = PointStruct(id="id1", payload={"content": "content"}, vector={"vector": [1.0, 2.0, 3.0]})
    else:
        record = PointStruct(id="id1", payload={"content": "content"}, vector=[1.0, 2.0, 3.0])
    ids = await collection._inner_upsert([record])
    assert ids[0] == "id1"

    ids = await collection.upsert(record={"id": "id1", "content": "content", "vector": [1.0, 2.0, 3.0]})
    assert ids == "id1"


@mark.asyncio
async def test_get(collection):
    records = await collection._inner_get(["id1"])
    assert records is not None

    records = await collection.get("id1")
    assert records is not None


@mark.asyncio
async def test_delete(collection):
    await collection._inner_delete(["id1"])


@mark.asyncio
async def test_does_collection_exist(collection):
    await collection.does_collection_exist()


@mark.asyncio
async def test_delete_collection(collection):
    await collection.delete_collection()


@mark.asyncio
@mark.parametrize(
    "collection_to_use, results",
    [
        (
            "collection",
            {
                "collection_name": "test",
                "vectors_config": {"vector": VectorParams(size=3, distance=Distance.COSINE, datatype=Datatype.FLOAT32)},
            },
        ),
        (
            "collection_without_named_vectors",
            {
                "collection_name": "test",
                "vectors_config": VectorParams(size=3, distance=Distance.COSINE, datatype=Datatype.FLOAT32),
            },
        ),
    ],
)
async def test_create_index_with_named_vectors(collection_to_use, results, mock_create_collection, request):
    await request.getfixturevalue(collection_to_use).create_collection()
    mock_create_collection.assert_called_once_with(**results)


@mark.asyncio
@mark.parametrize("collection_to_use", ["collection", "collection_without_named_vectors"])
async def test_create_index_fail(collection_to_use, request):
    collection = request.getfixturevalue(collection_to_use)
    collection.data_model_definition.fields["vector"].dimensions = None
    with raises(MemoryConnectorException, match="Vector field must have dimensions."):
        await collection.create_collection()
