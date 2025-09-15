# Copyright (c) Microsoft. All rights reserved.


from unittest.mock import AsyncMock

import pytest
from weaviate import WeaviateAsyncClient
from weaviate.collections.collections.async_ import _CollectionsAsync


@pytest.fixture
def collections_side_effects(request):
    """Fixture that returns a dictionary of side effects for the mock async client methods."""
    return request.param if hasattr(request, "param") else {}


@pytest.fixture()
def mock_async_client(collections_side_effects) -> AsyncMock:
    """Fixture to create a mock async client."""
    async_mock = AsyncMock(spec=WeaviateAsyncClient)
    async_mock.collections = AsyncMock(spec=_CollectionsAsync)
    async_mock.collections.create = AsyncMock()
    async_mock.collections.delete = AsyncMock()
    async_mock.collections.exists = AsyncMock()

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
