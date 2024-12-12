# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock

import pytest
from mistralai import Mistral
from mistralai.models import EmbeddingResponse

from semantic_kernel.connectors.ai.mistral_ai.services.mistral_ai_text_embedding import MistralAITextEmbedding
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError, ServiceResponseException


def test_embedding_with_env_variables(mistralai_unit_test_env):
    text_embedding = MistralAITextEmbedding()
    assert text_embedding.ai_model_id == "test_embedding_model_id"
    assert text_embedding.async_client.sdk_configuration.security.api_key == "test_api_key"


@pytest.mark.parametrize("exclude_list", [["MISTRALAI_API_KEY", "MISTRALAI_EMBEDDING_MODEL_ID"]], indirect=True)
def test_embedding_with_constructor(mistralai_unit_test_env):
    text_embedding = MistralAITextEmbedding(
        api_key="overwrite-api-key",
        ai_model_id="overwrite-model",
    )
    assert text_embedding.ai_model_id == "overwrite-model"
    assert text_embedding.async_client.sdk_configuration.security.api_key == "overwrite-api-key"


def test_embedding_with_client(mistralai_unit_test_env):
    client = MagicMock(spec=Mistral)
    text_embedding = MistralAITextEmbedding(async_client=client)
    assert text_embedding.async_client == client
    assert text_embedding.ai_model_id == "test_embedding_model_id"


def test_embedding_with_api_key(mistralai_unit_test_env):
    text_embedding = MistralAITextEmbedding(api_key="overwrite-api-key")
    assert text_embedding.async_client.sdk_configuration.security.api_key == "overwrite-api-key"
    assert text_embedding.ai_model_id == "test_embedding_model_id"


def test_embedding_with_model(mistralai_unit_test_env):
    text_embedding = MistralAITextEmbedding(ai_model_id="overwrite-model")
    assert text_embedding.ai_model_id == "overwrite-model"
    assert text_embedding.async_client.sdk_configuration.security.api_key == "test_api_key"


@pytest.mark.parametrize("exclude_list", [["MISTRALAI_EMBEDDING_MODEL_ID"]], indirect=True)
def test_embedding_with_model_without_env(mistralai_unit_test_env):
    text_embedding = MistralAITextEmbedding(ai_model_id="overwrite-model")
    assert text_embedding.ai_model_id == "overwrite-model"
    assert text_embedding.async_client.sdk_configuration.security.api_key == "test_api_key"


@pytest.mark.parametrize("exclude_list", [["MISTRALAI_EMBEDDING_MODEL_ID"]], indirect=True)
def test_embedding_missing_model(mistralai_unit_test_env):
    with pytest.raises(ServiceInitializationError):
        MistralAITextEmbedding(
            env_file_path="test.env",
        )


@pytest.mark.parametrize("exclude_list", [["MISTRALAI_API_KEY"]], indirect=True)
def test_embedding_missing_api_key(mistralai_unit_test_env):
    with pytest.raises(ServiceInitializationError):
        MistralAITextEmbedding(
            env_file_path="test.env",
        )


@pytest.mark.parametrize("exclude_list", [["MISTRALAI_API_KEY", "MISTRALAI_EMBEDDING_MODEL_ID"]], indirect=True)
def test_embedding_missing_api_key_constructor(mistralai_unit_test_env):
    with pytest.raises(ServiceInitializationError):
        MistralAITextEmbedding(
            env_file_path="test.env",
        )


@pytest.mark.parametrize("exclude_list", [["MISTRALAI_API_KEY", "MISTRALAI_EMBEDDING_MODEL_ID"]], indirect=True)
def test_embedding_missing_model_constructor(mistralai_unit_test_env):
    with pytest.raises(ServiceInitializationError):
        MistralAITextEmbedding(
            api_key="test_api_key",
            env_file_path="test.env",
        )


async def test_embedding_generate_raw_embedding(mistralai_unit_test_env):
    mock_client = AsyncMock(spec=Mistral)
    mock_client.embeddings = AsyncMock()
    mock_embedding_response = MagicMock(spec=EmbeddingResponse, data=[MagicMock(embedding=[1, 2, 3, 4, 5])])
    mock_client.embeddings.create_async.return_value = mock_embedding_response
    text_embedding = MistralAITextEmbedding(async_client=mock_client)
    embedding = await text_embedding.generate_raw_embeddings(["test"])
    assert embedding == [[1, 2, 3, 4, 5]]


async def test_embedding_generate_embedding(mistralai_unit_test_env):
    mock_client = AsyncMock(spec=Mistral)
    mock_client.embeddings = AsyncMock()
    mock_embedding_response = MagicMock(spec=EmbeddingResponse, data=[MagicMock(embedding=[1, 2, 3, 4, 5])])
    mock_client.embeddings.create_async.return_value = mock_embedding_response
    text_embedding = MistralAITextEmbedding(async_client=mock_client)
    embedding = await text_embedding.generate_embeddings(["test"])
    assert embedding.tolist() == [[1, 2, 3, 4, 5]]


async def test_embedding_generate_embedding_exception(mistralai_unit_test_env):
    mock_client = AsyncMock(spec=Mistral)
    mock_client.embeddings = AsyncMock()
    mock_client.embeddings.create_async.side_effect = Exception("Test Exception")
    text_embedding = MistralAITextEmbedding(async_client=mock_client)
    with pytest.raises(ServiceResponseException):
        await text_embedding.generate_embeddings(["test"])
