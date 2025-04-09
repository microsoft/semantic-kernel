# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch

import pytest
from openai import AsyncClient
from openai.resources.embeddings import AsyncEmbeddings

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIEmbeddingPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_embedding import OpenAITextEmbedding
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError, ServiceResponseException


def test_init(openai_unit_test_env):
    openai_text_embedding = OpenAITextEmbedding()

    assert openai_text_embedding.client is not None
    assert isinstance(openai_text_embedding.client, AsyncClient)
    assert openai_text_embedding.ai_model_id == openai_unit_test_env["OPENAI_EMBEDDING_MODEL_ID"]

    assert openai_text_embedding.get_prompt_execution_settings_class() == OpenAIEmbeddingPromptExecutionSettings


def test_init_validation_fail() -> None:
    with pytest.raises(ServiceInitializationError):
        OpenAITextEmbedding(api_key="34523", ai_model_id={"test": "dict"})


def test_init_to_from_dict(openai_unit_test_env):
    default_headers = {"X-Unit-Test": "test-guid"}

    settings = {
        "ai_model_id": openai_unit_test_env["OPENAI_EMBEDDING_MODEL_ID"],
        "api_key": openai_unit_test_env["OPENAI_API_KEY"],
        "default_headers": default_headers,
    }
    text_embedding = OpenAITextEmbedding.from_dict(settings)
    dumped_settings = text_embedding.to_dict()
    assert dumped_settings["ai_model_id"] == settings["ai_model_id"]
    assert dumped_settings["api_key"] == settings["api_key"]


@pytest.mark.parametrize("exclude_list", [["OPENAI_API_KEY"]], indirect=True)
def test_init_with_empty_api_key(openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        OpenAITextEmbedding(
            env_file_path="test.env",
        )


@pytest.mark.parametrize("exclude_list", [["OPENAI_EMBEDDING_MODEL_ID"]], indirect=True)
def test_init_with_no_model_id(openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        OpenAITextEmbedding(
            env_file_path="test.env",
        )


@patch.object(AsyncEmbeddings, "create", new_callable=AsyncMock)
async def test_embedding_calls_with_parameters(mock_create, openai_unit_test_env) -> None:
    ai_model_id = "test_model_id"
    texts = ["hello world", "goodbye world"]
    embedding_dimensions = 1536

    openai_text_embedding = OpenAITextEmbedding(
        ai_model_id=ai_model_id,
    )

    await openai_text_embedding.generate_embeddings(texts, dimensions=embedding_dimensions)

    mock_create.assert_awaited_once_with(
        input=texts,
        model=ai_model_id,
        dimensions=embedding_dimensions,
    )


@patch.object(AsyncEmbeddings, "create", new_callable=AsyncMock)
async def test_embedding_calls_with_settings(mock_create, openai_unit_test_env) -> None:
    ai_model_id = "test_model_id"
    texts = ["hello world", "goodbye world"]
    settings = OpenAIEmbeddingPromptExecutionSettings(service_id="default", dimensions=1536)
    openai_text_embedding = OpenAITextEmbedding(service_id="default", ai_model_id=ai_model_id)

    await openai_text_embedding.generate_embeddings(texts, settings=settings, timeout=10)

    mock_create.assert_awaited_once_with(
        input=texts,
        model=ai_model_id,
        dimensions=1536,
        timeout=10,
    )


@patch.object(AsyncEmbeddings, "create", new_callable=AsyncMock, side_effect=Exception)
async def test_embedding_fail(mock_create, openai_unit_test_env) -> None:
    ai_model_id = "test_model_id"
    texts = ["hello world", "goodbye world"]
    embedding_dimensions = 1536

    openai_text_embedding = OpenAITextEmbedding(
        ai_model_id=ai_model_id,
    )
    with pytest.raises(ServiceResponseException):
        await openai_text_embedding.generate_embeddings(texts, dimensions=embedding_dimensions)


@patch.object(AsyncEmbeddings, "create", new_callable=AsyncMock)
async def test_embedding_pes(mock_create, openai_unit_test_env) -> None:
    ai_model_id = "test_model_id"
    texts = ["hello world", "goodbye world"]
    embedding_dimensions = 1536
    pes = PromptExecutionSettings(ai_model_id=ai_model_id, dimensions=embedding_dimensions)

    openai_text_embedding = OpenAITextEmbedding(ai_model_id=ai_model_id)

    await openai_text_embedding.generate_raw_embeddings(texts, pes)

    mock_create.assert_awaited_once_with(
        input=texts,
        model=ai_model_id,
        dimensions=embedding_dimensions,
    )
