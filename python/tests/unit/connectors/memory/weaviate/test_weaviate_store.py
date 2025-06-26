# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import ANY, AsyncMock, patch

import pytest
from weaviate import WeaviateAsyncClient

from semantic_kernel.connectors.weaviate import WeaviateStore
from semantic_kernel.exceptions import ServiceInvalidExecutionSettingsError, VectorStoreInitializationException


@patch(
    "semantic_kernel.connectors.weaviate.use_async_with_weaviate_cloud",
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


@patch(
    "semantic_kernel.connectors.weaviate.use_async_with_local",
    return_value=AsyncMock(spec=WeaviateAsyncClient),
)
def test_weaviate_store_init_with_local(
    mock_use_weaviate_local,
    clear_weaviate_env,
) -> None:
    """Test the initialization of a WeaviateStore object with Weaviate local deployment."""
    store = WeaviateStore(
        local_host="localhost",
        env_file_path="fake_env_file_path.env",
    )

    assert store.async_client is not None
    mock_use_weaviate_local.assert_called_once_with(host="localhost")


@patch(
    "semantic_kernel.connectors.weaviate.use_async_with_embedded",
    return_value=AsyncMock(spec=WeaviateAsyncClient),
)
def test_weaviate_store_init_with_embedded(
    mock_use_weaviate_embedded,
    clear_weaviate_env,
    record_type,
    definition,
) -> None:
    """Test the initialization of a WeaviateStore object with Weaviate embedded deployment."""
    store = WeaviateStore(
        use_embed=True,
        env_file_path="fake_env_file_path.env",
    )

    assert store.async_client is not None
    mock_use_weaviate_embedded.assert_called_once()


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
    record_type,
    definition,
) -> None:
    """Test the initialization of a WeaviateStore object with a custom client."""
    store = WeaviateStore(
        async_client=AsyncMock(spec=WeaviateAsyncClient),
        env_file_path="fake_env_file_path.env",
    )

    assert store.async_client is not None


@patch(
    "semantic_kernel.connectors.weaviate.use_async_with_local",
    side_effect=Exception,
)
def test_weaviate_store_init_fail_to_create_client(
    clear_weaviate_env,
    record_type,
    definition,
) -> None:
    """Test the initialization of a WeaviateStore object raises an error when failing to create a client."""
    with pytest.raises(VectorStoreInitializationException):
        WeaviateStore(
            local_host="localhost",
            env_file_path="fake_env_file_path.env",
        )
