# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch

import pytest
from openai import AsyncClient
from openai.resources.embeddings import AsyncEmbeddings

from semantic_kernel.connectors.ai.nvidia.prompt_execution_settings.nvidia_prompt_execution_settings import (
    NvidiaEmbeddingPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.nvidia.services.nvidia_text_embedding import NvidiaTextEmbedding
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError, ServiceResponseException


@pytest.fixture
def nvidia_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for NvidiaTextEmbedding."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {"NVIDIA_API_KEY": "test_api_key", "NVIDIA_EMBEDDING_MODEL_ID": "test_embedding_model_id"}

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


def test_init(nvidia_unit_test_env):
    nvidia_text_embedding = NvidiaTextEmbedding()

    assert nvidia_text_embedding.client is not None
    assert isinstance(nvidia_text_embedding.client, AsyncClient)
    assert nvidia_text_embedding.ai_model_id == nvidia_unit_test_env["NVIDIA_EMBEDDING_MODEL_ID"]

    assert nvidia_text_embedding.get_prompt_execution_settings_class() == NvidiaEmbeddingPromptExecutionSettings


def test_init_validation_fail() -> None:
    with pytest.raises(ServiceInitializationError):
        NvidiaTextEmbedding(api_key="34523", ai_model_id={"test": "dict"})


def test_init_to_from_dict(nvidia_unit_test_env):
    default_headers = {"X-Unit-Test": "test-guid"}

    settings = {
        "ai_model_id": nvidia_unit_test_env["NVIDIA_EMBEDDING_MODEL_ID"],
        "api_key": nvidia_unit_test_env["NVIDIA_API_KEY"],
        "default_headers": default_headers,
    }
    text_embedding = NvidiaTextEmbedding.from_dict(settings)
    dumped_settings = text_embedding.to_dict()
    assert dumped_settings["ai_model_id"] == settings["ai_model_id"]
    assert dumped_settings["api_key"] == settings["api_key"]


@patch.object(AsyncEmbeddings, "create", new_callable=AsyncMock)
async def test_embedding_calls_with_parameters(mock_create, nvidia_unit_test_env) -> None:
    ai_model_id = "NV-Embed-QA"
    texts = ["hello world", "goodbye world"]
    embedding_dimensions = 1536

    nvidia_text_embedding = NvidiaTextEmbedding(
        ai_model_id=ai_model_id,
    )

    await nvidia_text_embedding.generate_embeddings(texts, dimensions=embedding_dimensions)

    mock_create.assert_awaited_once_with(
        input=texts,
        model=ai_model_id,
        dimensions=embedding_dimensions,
        encoding_format="float",
        extra_body={"input_type": "query", "truncate": "NONE"},
    )


@patch.object(AsyncEmbeddings, "create", new_callable=AsyncMock)
async def test_embedding_calls_with_settings(mock_create, nvidia_unit_test_env) -> None:
    ai_model_id = "test_model_id"
    texts = ["hello world", "goodbye world"]
    settings = NvidiaEmbeddingPromptExecutionSettings(service_id="default")
    nvidia_text_embedding = NvidiaTextEmbedding(service_id="default", ai_model_id=ai_model_id)

    await nvidia_text_embedding.generate_embeddings(texts, settings=settings)

    mock_create.assert_awaited_once_with(
        input=texts,
        model=ai_model_id,
        encoding_format="float",
        extra_body={"input_type": "query", "truncate": "NONE"},
    )


@patch.object(AsyncEmbeddings, "create", new_callable=AsyncMock, side_effect=Exception)
async def test_embedding_fail(mock_create, nvidia_unit_test_env) -> None:
    ai_model_id = "test_model_id"
    texts = ["hello world", "goodbye world"]

    nvidia_text_embedding = NvidiaTextEmbedding(
        ai_model_id=ai_model_id,
    )
    with pytest.raises(ServiceResponseException):
        await nvidia_text_embedding.generate_embeddings(texts)


@patch.object(AsyncEmbeddings, "create", new_callable=AsyncMock)
async def test_embedding_pes(mock_create, nvidia_unit_test_env) -> None:
    ai_model_id = "test_model_id"
    texts = ["hello world", "goodbye world"]

    pes = PromptExecutionSettings(service_id="x", ai_model_id=ai_model_id)

    nvidia_text_embedding = NvidiaTextEmbedding(ai_model_id=ai_model_id)

    await nvidia_text_embedding.generate_raw_embeddings(texts, pes)

    mock_create.assert_awaited_once_with(
        input=texts,
        model=ai_model_id,
        encoding_format="float",
        extra_body={"input_type": "query", "truncate": "NONE"},
    )
