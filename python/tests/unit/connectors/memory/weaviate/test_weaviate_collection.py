# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import ANY, AsyncMock, patch

import pytest
from weaviate import WeaviateAsyncClient
from weaviate.classes.config import Configure, DataType, Property
from weaviate.collections.classes.config_vectorizers import VectorDistances
from weaviate.collections.classes.data import DataObject

from semantic_kernel.connectors.weaviate import WeaviateCollection
from semantic_kernel.exceptions import (
    ServiceInvalidExecutionSettingsError,
    VectorStoreInitializationException,
    VectorStoreOperationException,
)


@patch(
    "semantic_kernel.connectors.weaviate.use_async_with_weaviate_cloud",
    return_value=AsyncMock(spec=WeaviateAsyncClient),
)
def test_weaviate_collection_init_with_weaviate_cloud(
    mock_use_weaviate_cloud,
    clear_weaviate_env,
    record_type,
    definition,
) -> None:
    """Test the initialization of a WeaviateCollection object with Weaviate Cloud."""
    collection_name = "TestCollection"

    collection = WeaviateCollection(
        record_type=record_type,
        definition=definition,
        collection_name=collection_name,
        url="https://test.cloud.weaviate.com/",
        api_key="test_api_key",
        env_file_path="fake_env_file_path.env",
    )

    assert collection.collection_name == collection_name
    assert collection.async_client is not None
    mock_use_weaviate_cloud.assert_called_once_with(
        cluster_url="https://test.cloud.weaviate.com/",
        auth_credentials=ANY,
    )


@patch(
    "semantic_kernel.connectors.weaviate.use_async_with_local",
    return_value=AsyncMock(spec=WeaviateAsyncClient),
)
def test_weaviate_collection_init_with_local(
    mock_use_weaviate_local,
    clear_weaviate_env,
    record_type,
    definition,
) -> None:
    """Test the initialization of a WeaviateCollection object with Weaviate local deployment."""
    collection_name = "TestCollection"

    collection = WeaviateCollection(
        record_type=record_type,
        definition=definition,
        collection_name=collection_name,
        local_host="localhost",
        env_file_path="fake_env_file_path.env",
    )

    assert collection.collection_name == collection_name
    assert collection.async_client is not None
    mock_use_weaviate_local.assert_called_once_with(host="localhost")


@patch(
    "semantic_kernel.connectors.weaviate.use_async_with_embedded",
    return_value=AsyncMock(spec=WeaviateAsyncClient),
)
def test_weaviate_collection_init_with_embedded(
    mock_use_weaviate_embedded,
    clear_weaviate_env,
    record_type,
    definition,
) -> None:
    """Test the initialization of a WeaviateCollection object with Weaviate embedded deployment."""
    collection_name = "TestCollection"

    collection = WeaviateCollection(
        record_type=record_type,
        definition=definition,
        collection_name=collection_name,
        use_embed=True,
        env_file_path="fake_env_file_path.env",
    )

    assert collection.collection_name == collection_name
    assert collection.async_client is not None
    mock_use_weaviate_embedded.assert_called_once()


def test_weaviate_collection_init_with_invalid_settings_more_than_one_backends(
    weaviate_unit_test_env,
    record_type,
    definition,
) -> None:
    """Test the initialization of a WeaviateCollection object with multiple backend options enabled."""
    collection_name = "TestCollection"

    with pytest.raises(ServiceInvalidExecutionSettingsError):
        WeaviateCollection(
            record_type=record_type,
            definition=definition,
            collection_name=collection_name,
            env_file_path="fake_env_file_path.env",
        )


def test_weaviate_collection_init_with_invalid_settings_no_backends(
    clear_weaviate_env,
    record_type,
    definition,
) -> None:
    """Test the initialization of a WeaviateCollection object with no backend options enabled."""
    collection_name = "TestCollection"

    with pytest.raises(ServiceInvalidExecutionSettingsError):
        WeaviateCollection(
            record_type=record_type,
            definition=definition,
            collection_name=collection_name,
            env_file_path="fake_env_file_path.env",
        )


def test_weaviate_collection_init_with_custom_client(
    clear_weaviate_env,
    record_type,
    definition,
) -> None:
    """Test the initialization of a WeaviateCollection object with a custom client."""
    collection_name = "TestCollection"

    collection = WeaviateCollection(
        record_type=record_type,
        definition=definition,
        collection_name=collection_name,
        async_client=AsyncMock(spec=WeaviateAsyncClient),
        env_file_path="fake_env_file_path.env",
    )

    assert collection.collection_name == collection_name
    assert collection.async_client is not None


@patch(
    "semantic_kernel.connectors.weaviate.use_async_with_local",
    side_effect=Exception,
)
def test_weaviate_collection_init_fail_to_create_client(
    clear_weaviate_env,
    record_type,
    definition,
) -> None:
    """Test the initialization of a WeaviateCollection object raises an error when failing to create a client."""
    collection_name = "TestCollection"

    with pytest.raises(VectorStoreInitializationException):
        WeaviateCollection(
            record_type=record_type,
            definition=definition,
            collection_name=collection_name,
            local_host="localhost",
            env_file_path="fake_env_file_path.env",
        )


@patch(
    "semantic_kernel.connectors.weaviate.use_async_with_weaviate_cloud",
    return_value=AsyncMock(spec=WeaviateAsyncClient),
)
def test_weaviate_collection_init_with_lower_case_collection_name(
    mock_use_weaviate_cloud,
    clear_weaviate_env,
    record_type,
    definition,
) -> None:
    """Test a collection name with lower case letters."""
    collection_name = "testCollection"

    collection = WeaviateCollection(
        record_type=record_type,
        definition=definition,
        collection_name=collection_name,
        url="https://test.cloud.weaviate.com",
        api_key="test_api_key",
        env_file_path="fake_env_file_path.env",
    )

    assert collection.collection_name[0].isupper()
    assert collection.async_client is not None


@pytest.mark.parametrize("index_kind, distance_function", [("hnsw", "cosine_distance")])
async def test_weaviate_collection_create_collection(
    clear_weaviate_env,
    record_type,
    definition,
    mock_async_client,
) -> None:
    """Test the creation of a collection in Weaviate."""
    collection_name = "TestCollection"

    collection = WeaviateCollection(
        record_type=record_type,
        definition=definition,
        collection_name=collection_name,
        async_client=mock_async_client,
        env_file_path="fake_env_file_path.env",
    )

    await collection.create_collection()

    mock_async_client.collections.create.assert_called_once_with(
        name=collection_name,
        properties=[
            Property(
                name="content",
                data_type=DataType.TEXT,
            )
        ],
        vector_index_config=None,
        vectorizer_config=[
            Configure.NamedVectors.none(
                name="vector",
                vector_index_config=Configure.VectorIndex.hnsw(distance_metric=VectorDistances.COSINE),
            )
        ],
    )


@pytest.mark.parametrize(
    "collections_side_effects",
    [
        {"create": Exception},
    ],
    indirect=True,
)
async def test_weaviate_collection_create_collection_fail(
    mock_async_client,
    clear_weaviate_env,
    record_type,
    definition,
) -> None:
    """Test failing to create a collection in Weaviate."""
    collection_name = "TestCollection"

    collection = WeaviateCollection(
        record_type=record_type,
        definition=definition,
        collection_name=collection_name,
        async_client=mock_async_client,
        env_file_path="fake_env_file_path.env",
    )

    with pytest.raises(VectorStoreOperationException):
        await collection.create_collection()


async def test_weaviate_collection_delete_collection(
    clear_weaviate_env,
    record_type,
    definition,
    mock_async_client,
) -> None:
    """Test the deletion of a collection in Weaviate."""
    collection_name = "TestCollection"

    collection = WeaviateCollection(
        record_type=record_type,
        definition=definition,
        collection_name=collection_name,
        async_client=mock_async_client,
        env_file_path="fake_env_file_path.env",
    )

    await collection.ensure_collection_deleted()

    mock_async_client.collections.delete.assert_called_once_with(collection_name)


@pytest.mark.parametrize(
    "collections_side_effects",
    [
        {"delete": Exception},
    ],
    indirect=True,
)
async def test_weaviate_collection_delete_collection_fail(
    mock_async_client,
    clear_weaviate_env,
    record_type,
    definition,
) -> None:
    """Test failing to delete a collection in Weaviate."""
    collection_name = "TestCollection"

    collection = WeaviateCollection(
        record_type=record_type,
        definition=definition,
        collection_name=collection_name,
        async_client=mock_async_client,
        env_file_path="fake_env_file_path.env",
    )

    with pytest.raises(VectorStoreOperationException):
        await collection.ensure_collection_deleted()


async def test_weaviate_collection_collection_exist(
    clear_weaviate_env,
    record_type,
    definition,
    mock_async_client,
) -> None:
    """Test checking if a collection exists in Weaviate."""
    collection_name = "TestCollection"

    collection = WeaviateCollection(
        record_type=record_type,
        definition=definition,
        collection_name=collection_name,
        async_client=mock_async_client,
        env_file_path="fake_env_file_path.env",
    )

    await collection.does_collection_exist()

    mock_async_client.collections.exists.assert_called_once_with(collection_name)


@pytest.mark.parametrize(
    "collections_side_effects",
    [
        {"exists": Exception},
    ],
    indirect=True,
)
async def test_weaviate_collection_collection_exist_fail(
    mock_async_client,
    clear_weaviate_env,
    record_type,
    definition,
) -> None:
    """Test failing to check if a collection exists in Weaviate."""
    collection_name = "TestCollection"

    collection = WeaviateCollection(
        record_type=record_type,
        definition=definition,
        collection_name=collection_name,
        async_client=mock_async_client,
        env_file_path="fake_env_file_path.env",
    )

    with pytest.raises(VectorStoreOperationException):
        await collection.does_collection_exist()


async def test_weaviate_collection_serialize_data(
    mock_async_client,
    clear_weaviate_env,
    record_type,
    definition,
    dataclass_vector_data_model,
) -> None:
    """Test upserting data into a collection in Weaviate."""
    collection_name = "TestCollection"

    collection = WeaviateCollection(
        record_type=record_type,
        definition=definition,
        collection_name=collection_name,
        async_client=mock_async_client,
        env_file_path="fake_env_file_path.env",
    )

    with patch.object(collection, "_inner_upsert") as mock_inner_upsert:
        data = dataclass_vector_data_model()
        await collection.upsert(data)

        mock_inner_upsert.assert_called_once_with([
            DataObject(
                properties={"content": "content1"},
                uuid=data.id,
                vector={"vector": data.vector},
                references=None,
            )
        ])


async def test_weaviate_collection_deserialize_data(
    mock_async_client,
    clear_weaviate_env,
    record_type,
    definition,
    dataclass_vector_data_model,
) -> None:
    """Test getting data from a collection in Weaviate."""
    collection_name = "TestCollection"

    collection = WeaviateCollection(
        record_type=record_type,
        definition=definition,
        collection_name=collection_name,
        async_client=mock_async_client,
        env_file_path="fake_env_file_path.env",
    )

    data = dataclass_vector_data_model()
    weaviate_data_object = DataObject(
        properties={"content": "content1"},
        uuid=data.id,
        vector={"vector": data.vector or [1, 2, 3]},
    )

    with patch.object(collection, "_inner_get", return_value=[weaviate_data_object]) as mock_inner_get:
        await collection.get(key=data.id)

        mock_inner_get.assert_called_once_with([data.id], include_vectors=False, options=None)
