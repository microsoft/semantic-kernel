# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import ANY, AsyncMock, patch

import pytest
import weaviate
from weaviate import WeaviateAsyncClient
from weaviate.classes.config import Configure, DataType, Property
from weaviate.collections.classes.data import DataObject

from semantic_kernel.connectors.memory.weaviate.weaviate_collection import WeaviateCollection
from semantic_kernel.exceptions.memory_connector_exceptions import (
    MemoryConnectorException,
    MemoryConnectorInitializationError,
)
from semantic_kernel.exceptions.service_exceptions import ServiceInvalidExecutionSettingsError


@patch.object(
    weaviate,
    "use_async_with_weaviate_cloud",
    return_value=AsyncMock(spec=WeaviateAsyncClient),
)
def test_weaviate_collection_init_with_weaviate_cloud(
    mock_use_weaviate_cloud,
    clear_weaviate_env,
    data_model_type,
    data_model_definition,
) -> None:
    """Test the initialization of a WeaviateCollection object with Weaviate Cloud."""
    collection_name = "TestCollection"

    collection = WeaviateCollection(
        data_model_type=data_model_type,
        data_model_definition=data_model_definition,
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


@patch.object(
    weaviate,
    "use_async_with_local",
    return_value=AsyncMock(spec=WeaviateAsyncClient),
)
def test_weaviate_collection_init_with_local(
    mock_use_weaviate_cloud,
    clear_weaviate_env,
    data_model_type,
    data_model_definition,
) -> None:
    """Test the initialization of a WeaviateCollection object with Weaviate local deployment."""
    collection_name = "TestCollection"

    collection = WeaviateCollection(
        data_model_type=data_model_type,
        data_model_definition=data_model_definition,
        collection_name=collection_name,
        local_host="localhost",
        env_file_path="fake_env_file_path.env",
    )

    assert collection.collection_name == collection_name
    assert collection.async_client is not None
    mock_use_weaviate_cloud.assert_called_once_with(host="localhost")


@patch.object(
    weaviate,
    "use_async_with_embedded",
    return_value=AsyncMock(spec=WeaviateAsyncClient),
)
def test_weaviate_collection_init_with_embedded(
    mock_use_weaviate_cloud,
    clear_weaviate_env,
    data_model_type,
    data_model_definition,
) -> None:
    """Test the initialization of a WeaviateCollection object with Weaviate embedded deployment."""
    collection_name = "TestCollection"

    collection = WeaviateCollection(
        data_model_type=data_model_type,
        data_model_definition=data_model_definition,
        collection_name=collection_name,
        use_embed=True,
        env_file_path="fake_env_file_path.env",
    )

    assert collection.collection_name == collection_name
    assert collection.async_client is not None
    mock_use_weaviate_cloud.assert_called_once()


def test_weaviate_collection_init_with_invalid_settings_more_than_one_backends(
    weaviate_unit_test_env,
    data_model_type,
    data_model_definition,
) -> None:
    """Test the initialization of a WeaviateCollection object with multiple backend options enabled."""
    collection_name = "TestCollection"

    with pytest.raises(ServiceInvalidExecutionSettingsError):
        WeaviateCollection(
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            collection_name=collection_name,
            env_file_path="fake_env_file_path.env",
        )


def test_weaviate_collection_init_with_invalid_settings_no_backends(
    clear_weaviate_env,
    data_model_type,
    data_model_definition,
) -> None:
    """Test the initialization of a WeaviateCollection object with no backend options enabled."""
    collection_name = "TestCollection"

    with pytest.raises(ServiceInvalidExecutionSettingsError):
        WeaviateCollection(
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            collection_name=collection_name,
            env_file_path="fake_env_file_path.env",
        )


def test_weaviate_collection_init_with_custom_client(
    clear_weaviate_env,
    data_model_type,
    data_model_definition,
) -> None:
    """Test the initialization of a WeaviateCollection object with a custom client."""
    collection_name = "TestCollection"

    collection = WeaviateCollection(
        data_model_type=data_model_type,
        data_model_definition=data_model_definition,
        collection_name=collection_name,
        async_client=AsyncMock(spec=WeaviateAsyncClient),
        env_file_path="fake_env_file_path.env",
    )

    assert collection.collection_name == collection_name
    assert collection.async_client is not None


@patch.object(
    weaviate,
    "use_async_with_local",
    side_effect=Exception,
)
def test_weaviate_collection_init_fail_to_create_client(
    clear_weaviate_env,
    data_model_type,
    data_model_definition,
) -> None:
    """Test the initialization of a WeaviateCollection object raises an error when failing to create a client."""
    collection_name = "TestCollection"

    with pytest.raises(MemoryConnectorInitializationError):
        WeaviateCollection(
            data_model_type=data_model_type,
            data_model_definition=data_model_definition,
            collection_name=collection_name,
            local_host="localhost",
            env_file_path="fake_env_file_path.env",
        )


@patch.object(
    weaviate,
    "use_async_with_weaviate_cloud",
    return_value=AsyncMock(spec=WeaviateAsyncClient),
)
def test_weaviate_collection_init_with_lower_case_collection_name(
    mock_use_weaviate_cloud,
    clear_weaviate_env,
    data_model_type,
    data_model_definition,
) -> None:
    """Test a collection name with lower case letters."""
    collection_name = "testCollection"

    collection = WeaviateCollection(
        data_model_type=data_model_type,
        data_model_definition=data_model_definition,
        collection_name=collection_name,
        url="https://test.cloud.weaviate.com",
        api_key="test_api_key",
        env_file_path="fake_env_file_path.env",
    )

    assert collection.collection_name[0].isupper()
    assert collection.async_client is not None


@pytest.mark.asyncio
async def test_weaviate_collection_create_collection(
    clear_weaviate_env,
    data_model_type,
    data_model_definition,
    mock_async_client,
) -> None:
    """Test the creation of a collection in Weaviate."""
    collection_name = "TestCollection"

    collection = WeaviateCollection(
        data_model_type=data_model_type,
        data_model_definition=data_model_definition,
        collection_name=collection_name,
        async_client=mock_async_client,
        env_file_path="fake_env_file_path.env",
    )

    await collection.create_collection()

    mock_async_client.collections.create.assert_called_once_with(
        collection_name,
        properties=[
            Property(
                name="content",
                data_type=DataType.TEXT,
            )
        ],
        vectorizer_config=[
            Configure.NamedVectors.none(
                name="vector",
                vector_index_config=Configure.VectorIndex.none(),
            )
        ],
    )


@pytest.mark.asyncio
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
    data_model_type,
    data_model_definition,
) -> None:
    """Test failing to create a collection in Weaviate."""
    collection_name = "TestCollection"

    collection = WeaviateCollection(
        data_model_type=data_model_type,
        data_model_definition=data_model_definition,
        collection_name=collection_name,
        async_client=mock_async_client,
        env_file_path="fake_env_file_path.env",
    )

    with pytest.raises(MemoryConnectorException):
        await collection.create_collection()


@pytest.mark.asyncio
async def test_weaviate_collection_delete_collection(
    clear_weaviate_env,
    data_model_type,
    data_model_definition,
    mock_async_client,
) -> None:
    """Test the deletion of a collection in Weaviate."""
    collection_name = "TestCollection"

    collection = WeaviateCollection(
        data_model_type=data_model_type,
        data_model_definition=data_model_definition,
        collection_name=collection_name,
        async_client=mock_async_client,
        env_file_path="fake_env_file_path.env",
    )

    await collection.delete_collection()

    mock_async_client.collections.delete.assert_called_once_with(collection_name)


@pytest.mark.asyncio
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
    data_model_type,
    data_model_definition,
) -> None:
    """Test failing to delete a collection in Weaviate."""
    collection_name = "TestCollection"

    collection = WeaviateCollection(
        data_model_type=data_model_type,
        data_model_definition=data_model_definition,
        collection_name=collection_name,
        async_client=mock_async_client,
        env_file_path="fake_env_file_path.env",
    )

    with pytest.raises(MemoryConnectorException):
        await collection.delete_collection()


@pytest.mark.asyncio
async def test_weaviate_collection_collection_exist(
    clear_weaviate_env,
    data_model_type,
    data_model_definition,
    mock_async_client,
) -> None:
    """Test checking if a collection exists in Weaviate."""
    collection_name = "TestCollection"

    collection = WeaviateCollection(
        data_model_type=data_model_type,
        data_model_definition=data_model_definition,
        collection_name=collection_name,
        async_client=mock_async_client,
        env_file_path="fake_env_file_path.env",
    )

    await collection.does_collection_exist()

    mock_async_client.collections.exists.assert_called_once_with(collection_name)


@pytest.mark.asyncio
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
    data_model_type,
    data_model_definition,
) -> None:
    """Test failing to check if a collection exists in Weaviate."""
    collection_name = "TestCollection"

    collection = WeaviateCollection(
        data_model_type=data_model_type,
        data_model_definition=data_model_definition,
        collection_name=collection_name,
        async_client=mock_async_client,
        env_file_path="fake_env_file_path.env",
    )

    with pytest.raises(MemoryConnectorException):
        await collection.does_collection_exist()


@pytest.mark.asyncio
async def test_weaviate_collection_serialize_data(
    mock_async_client,
    clear_weaviate_env,
    data_model_type,
    data_model_definition,
    dataclass_vector_data_model,
) -> None:
    """Test upserting data into a collection in Weaviate."""
    collection_name = "TestCollection"

    collection = WeaviateCollection(
        data_model_type=data_model_type,
        data_model_definition=data_model_definition,
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
                vector={"content": data.vector},
                references=None,
            )
        ])


@pytest.mark.asyncio
async def test_weaviate_collection_deserialize_data(
    mock_async_client,
    clear_weaviate_env,
    data_model_type,
    data_model_definition,
    dataclass_vector_data_model,
) -> None:
    """Test getting data from a collection in Weaviate."""
    collection_name = "TestCollection"

    collection = WeaviateCollection(
        data_model_type=data_model_type,
        data_model_definition=data_model_definition,
        collection_name=collection_name,
        async_client=mock_async_client,
        env_file_path="fake_env_file_path.env",
    )

    data = dataclass_vector_data_model()
    weaviate_data_object = DataObject(
        properties={"content": "content1"},
        uuid=data.id,
        vector={"content": data.vector or [1, 2, 3]},
    )

    with patch.object(collection, "_inner_get", return_value=[weaviate_data_object]) as mock_inner_get:
        await collection.get(data.id)

        mock_inner_get.assert_called_once_with([data.id], include_vectors=True)
