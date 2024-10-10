# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch

import pytest
import weaviate

from semantic_kernel.connectors.memory.weaviate.weaviate_collection import WeaviateCollection


@pytest.fixture
def weaviate_cloud_url() -> str:
    return "https://test.cloud.weaviate.com"


@pytest.fixture
def weaviate_cloud_api_key() -> str:
    return "test_api_key"


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
        "WEAVIATE_LOCAL_PORT": "8080",
        "WEAVIATE_LOCAL_GRPC_PORT": "8081",
        "WEAVIATE_USE_EMBED": "true",
    }

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


# region Weaviate Collection


@pytest.mark.parametrize(
    "exclude_list",
    [
        [
            "WEAVIATE_URL",
            "WEAVIATE_API_KEY",
            "WEAVIATE_LOCAL_HOST",
            "WEAVIATE_LOCAL_PORT",
            "WEAVIATE_LOCAL_GRPC_PORT",
            "WEAVIATE_USE_EMBED",
        ]
    ],
    indirect=True,
)
@patch.object(
    weaviate,
    "use_async_with_weaviate_cloud",
    return_value=AsyncMock(spec=weaviate.WeaviateAsyncClient),
)
def test_weaviate_collection_init_with_weaviate_cloud(
    mock_use_weaviate_cloud,
    weaviate_unit_test_env,
    data_model_type,
    data_model_definition,
    weaviate_cloud_url,
    weaviate_cloud_api_key,
) -> None:
    """Test the initialization of a WeaviateCollection object with Weaviate Cloud."""
    collection_name = "TestCollection"

    collection = WeaviateCollection(
        data_model_type=data_model_type,
        data_model_definition=data_model_definition,
        collection_name=collection_name,
        url=weaviate_cloud_url,
        api_key=weaviate_cloud_api_key,
        env_file_path="fake_env_file_path.env",
    )

    assert collection.collection_name == collection_name
    assert collection.async_client is not None


@pytest.mark.parametrize(
    "exclude_list",
    [
        [
            "WEAVIATE_URL",
            "WEAVIATE_API_KEY",
            "WEAVIATE_LOCAL_HOST",
            "WEAVIATE_LOCAL_PORT",
            "WEAVIATE_LOCAL_GRPC_PORT",
            "WEAVIATE_USE_EMBED",
        ]
    ],
    indirect=True,
)
@patch.object(
    weaviate,
    "use_async_with_weaviate_cloud",
    return_value=AsyncMock(spec=weaviate.WeaviateAsyncClient),
)
def test_weaviate_collection_init_with_weaviate_cloud_lower_case_collection_name(
    mock_use_weaviate_cloud,
    weaviate_unit_test_env,
    data_model_type,
    data_model_definition,
    weaviate_cloud_url,
    weaviate_cloud_api_key,
) -> None:
    """Test a collection name with lower case letters."""
    collection_name = "testCollection"

    collection = WeaviateCollection(
        data_model_type=data_model_type,
        data_model_definition=data_model_definition,
        collection_name=collection_name,
        url=weaviate_cloud_url,
        api_key=weaviate_cloud_api_key,
        env_file_path="fake_env_file_path.env",
    )

    assert collection.collection_name == collection_name[0].upper() + collection_name[1:]
    assert collection.async_client is not None


# endregion

# region Weaviate Store

# endregion
