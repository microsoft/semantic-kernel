# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import ANY, AsyncMock, patch

import pytest
import weaviate
from weaviate import WeaviateAsyncClient
from weaviate.classes.config import Configure, DataType, Property
from weaviate.collections.classes.config_vectorizers import VectorDistances
from weaviate.collections.classes.data import DataObject
from weaviate.collections.collections.async_ import _CollectionsAsync

from semantic_kernel.connectors.memory.weaviate.utils import to_weaviate_vector_distance
from semantic_kernel.connectors.memory.weaviate.weaviate_collection import WeaviateCollection
from semantic_kernel.connectors.memory.weaviate.weaviate_store import WeaviateStore
from semantic_kernel.data.const import DistanceFunction
from semantic_kernel.exceptions.memory_connector_exceptions import (
    MemoryConnectorException,
    MemoryConnectorInitializationError,
)
from semantic_kernel.exceptions.service_exceptions import ServiceInvalidExecutionSettingsError


@pytest.fixture
def collections_side_effects(request):
    """Fixture that returns a dictionary of side effects for the mock async client methods."""
    return request.param if hasattr(request, "param") else {}


@pytest.fixture()
def mock_async_client(collections_side_effects) -> AsyncMock:
    """Fixture to create a mock async client."""
    async_mock = AsyncMock(spec=WeaviateAsyncClient)
    async_mock.collections = AsyncMock(spec=_CollectionsAsync)

    if collections_side_effects:
        for method_name, exception in collections_side_effects.items():
            getattr(async_mock.collections, method_name).side_effect = exception

    return async_mock


@pytest.fixture()
def weaviate_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for Weaviate unit tests."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {
        "WEAVIATE_URL": "test-api-key",
        "WEAVIATE_API_KEY": "https://test-endpoint.com",
        "WEAVIATE_LOCAL_HOST": "localhost",
        "WEAVIATE_LOCAL_PORT": 8080,
        "WEAVIATE_LOCAL_GRPC_PORT": 8081,
        "WEAVIATE_USE_EMBED": True,
    }

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@pytest.fixture()
def clear_weaviate_env(monkeypatch):
    """Fixture to clear the environment variables for Weaviate unit tests."""
    monkeypatch.delenv("WEAVIATE_URL", raising=False)
    monkeypatch.delenv("WEAVIATE_API_KEY", raising=False)
    monkeypatch.delenv("WEAVIATE_LOCAL_HOST", raising=False)
    monkeypatch.delenv("WEAVIATE_LOCAL_PORT", raising=False)
    monkeypatch.delenv("WEAVIATE_LOCAL_GRPC_PORT", raising=False)
    monkeypatch.delenv("WEAVIATE_USE_EMBED", raising=False)


# region Weaviate Collection


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


# endregion


# region Weaviate Store
@patch.object(
    weaviate,
    "use_async_with_weaviate_cloud",
    return_value=AsyncMock(spec=WeaviateAsyncClient),
)
def test_weaviate_store_init_with_weaviate_cloud(
    mock_use_weaviate_cloud,
    clear_weaviate_env,
) -> None:
    """Test the initialization of a WeaviateStore object with Weaviate Cloud."""
    store = WeaviateStore(
        url="https://test.cloud.weaviate.com/",
        api_key="test_api_key",
        env_file_path="fake_env_file_path.env",
    )

    assert store.async_client is not None
    mock_use_weaviate_cloud.assert_called_once_with(
        cluster_url="https://test.cloud.weaviate.com/",
        auth_credentials=ANY,
    )


@patch.object(
    weaviate,
    "use_async_with_local",
    return_value=AsyncMock(spec=WeaviateAsyncClient),
)
def test_weaviate_store_init_with_local(
    mock_use_weaviate_cloud,
    clear_weaviate_env,
) -> None:
    """Test the initialization of a WeaviateStore object with Weaviate local deployment."""
    store = WeaviateStore(
        local_host="localhost",
        env_file_path="fake_env_file_path.env",
    )

    assert store.async_client is not None
    mock_use_weaviate_cloud.assert_called_once_with(host="localhost")


@patch.object(
    weaviate,
    "use_async_with_embedded",
    return_value=AsyncMock(spec=WeaviateAsyncClient),
)
def test_weaviate_store_init_with_embedded(
    mock_use_weaviate_cloud,
    clear_weaviate_env,
    data_model_type,
    data_model_definition,
) -> None:
    """Test the initialization of a WeaviateStore object with Weaviate embedded deployment."""
    store = WeaviateStore(
        use_embed=True,
        env_file_path="fake_env_file_path.env",
    )

    assert store.async_client is not None
    mock_use_weaviate_cloud.assert_called_once()


def test_weaviate_store_init_with_invalid_settings_more_than_one_backends(
    weaviate_unit_test_env,
) -> None:
    """Test the initialization of a WeaviateStore object with multiple backend options enabled."""
    with pytest.raises(ServiceInvalidExecutionSettingsError):
        WeaviateStore(
            env_file_path="fake_env_file_path.env",
        )


def test_weaviate_store_init_with_invalid_settings_no_backends(
    clear_weaviate_env,
) -> None:
    """Test the initialization of a WeaviateStore object with no backend options enabled."""
    with pytest.raises(ServiceInvalidExecutionSettingsError):
        WeaviateStore(
            env_file_path="fake_env_file_path.env",
        )


def test_weaviate_store_init_with_custom_client(
    clear_weaviate_env,
    data_model_type,
    data_model_definition,
) -> None:
    """Test the initialization of a WeaviateStore object with a custom client."""
    store = WeaviateStore(
        async_client=AsyncMock(spec=WeaviateAsyncClient),
        env_file_path="fake_env_file_path.env",
    )

    assert store.async_client is not None


@patch.object(
    weaviate,
    "use_async_with_local",
    side_effect=Exception,
)
def test_weaviate_store_init_fail_to_create_client(
    clear_weaviate_env,
    data_model_type,
    data_model_definition,
) -> None:
    """Test the initialization of a WeaviateStore object raises an error when failing to create a client."""
    with pytest.raises(MemoryConnectorInitializationError):
        WeaviateStore(
            local_host="localhost",
            env_file_path="fake_env_file_path.env",
        )


# endregion

# region utility functions


def test_distance_function_mapping() -> None:
    """Test the distance function mapping."""

    assert to_weaviate_vector_distance(DistanceFunction.COSINE) == VectorDistances.COSINE
    assert to_weaviate_vector_distance(DistanceFunction.DOT_PROD) == VectorDistances.DOT
    assert to_weaviate_vector_distance(DistanceFunction.EUCLIDEAN) == VectorDistances.L2_SQUARED
    assert to_weaviate_vector_distance(DistanceFunction.MANHATTAN) == VectorDistances.MANHATTAN
    assert to_weaviate_vector_distance(DistanceFunction.HAMMING) == VectorDistances.HAMMING


# endregion
