# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch

import pytest
from azure.ai.inference.aio import EmbeddingsClient
from azure.core.credentials import AzureKeyCredential

from semantic_kernel.connectors.ai.azure_ai_inference import (
    AzureAIInferenceEmbeddingPromptExecutionSettings,
    AzureAIInferenceTextEmbedding,
)
from semantic_kernel.connectors.ai.azure_ai_inference.azure_ai_inference_settings import AzureAIInferenceSettings
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError
from semantic_kernel.utils.telemetry.user_agent import SEMANTIC_KERNEL_USER_AGENT


def test_azure_ai_inference_text_embedding_init(azure_ai_inference_unit_test_env, model_id) -> None:
    """Test initialization of AzureAIInferenceTextEmbedding"""
    azure_ai_inference = AzureAIInferenceTextEmbedding(model_id)

    assert azure_ai_inference.ai_model_id == model_id
    assert azure_ai_inference.service_id == model_id
    assert isinstance(azure_ai_inference.client, EmbeddingsClient)


@patch("azure.ai.inference.aio.EmbeddingsClient.__init__", return_value=None)
def test_azure_ai_inference_text_embedding_client_init(mock_client, azure_ai_inference_unit_test_env, model_id) -> None:
    """Test initialization of the Azure AI Inference client"""
    endpoint = azure_ai_inference_unit_test_env["AZURE_AI_INFERENCE_ENDPOINT"]
    api_key = azure_ai_inference_unit_test_env["AZURE_AI_INFERENCE_API_KEY"]
    settings = AzureAIInferenceSettings(endpoint=endpoint, api_key=api_key)

    _ = AzureAIInferenceTextEmbedding(model_id)

    assert mock_client.call_count == 1
    assert isinstance(mock_client.call_args.kwargs["endpoint"], str)
    assert mock_client.call_args.kwargs["endpoint"] == str(settings.endpoint)
    assert isinstance(mock_client.call_args.kwargs["credential"], AzureKeyCredential)
    assert mock_client.call_args.kwargs["credential"].key == settings.api_key.get_secret_value()
    assert mock_client.call_args.kwargs["user_agent"] == SEMANTIC_KERNEL_USER_AGENT


def test_azure_ai_inference_text_embedding_init_with_service_id(
    azure_ai_inference_unit_test_env, model_id, service_id
) -> None:
    """Test initialization of AzureAIInferenceTextEmbedding"""
    azure_ai_inference = AzureAIInferenceTextEmbedding(model_id, service_id=service_id)

    assert azure_ai_inference.ai_model_id == model_id
    assert azure_ai_inference.service_id == service_id
    assert isinstance(azure_ai_inference.client, EmbeddingsClient)


@pytest.mark.parametrize(
    "azure_ai_inference_client",
    [AzureAIInferenceTextEmbedding.__name__],
    indirect=True,
)
def test_azure_ai_inference_chat_completion_init_with_custom_client(azure_ai_inference_client, model_id) -> None:
    """Test initialization of AzureAIInferenceTextEmbedding with custom client"""
    client = azure_ai_inference_client
    azure_ai_inference = AzureAIInferenceTextEmbedding(model_id, client=client)

    assert azure_ai_inference.ai_model_id == model_id
    assert azure_ai_inference.service_id == model_id
    assert azure_ai_inference.client == client


@pytest.mark.parametrize("exclude_list", [["AZURE_AI_INFERENCE_ENDPOINT"]], indirect=True)
def test_azure_ai_inference_text_embedding_init_with_empty_endpoint(azure_ai_inference_unit_test_env, model_id) -> None:
    """Test initialization of AzureAIInferenceTextEmbedding with empty endpoint"""
    with pytest.raises(ServiceInitializationError):
        AzureAIInferenceTextEmbedding(model_id, env_file_path="fake_path")


@pytest.mark.parametrize(
    "azure_ai_inference_service",
    [AzureAIInferenceTextEmbedding.__name__],
    indirect=True,
)
@patch.object(EmbeddingsClient, "embed", new_callable=AsyncMock)
async def test_azure_ai_inference_text_embedding(
    mock_embed,
    azure_ai_inference_service,
    model_id,
) -> None:
    """Test text embedding generation of AzureAIInferenceTextEmbedding without settings"""
    texts = ["hello", "world"]
    await azure_ai_inference_service.generate_embeddings(texts)

    mock_embed.assert_awaited_once_with(
        input=texts,
        model=model_id,
        model_extras=None,
        dimensions=None,
        encoding_format=None,
        input_type=None,
    )


@pytest.mark.parametrize(
    "azure_ai_inference_service",
    [AzureAIInferenceTextEmbedding.__name__],
    indirect=True,
)
@patch.object(EmbeddingsClient, "embed", new_callable=AsyncMock)
async def test_azure_ai_inference_text_embedding_with_standard_settings(
    mock_embed,
    azure_ai_inference_service,
    model_id,
) -> None:
    """Test text embedding generation of AzureAIInferenceTextEmbedding with standard settings"""
    texts = ["hello", "world"]
    settings = AzureAIInferenceEmbeddingPromptExecutionSettings(
        dimensions=1024, encoding_format="float", input_type="text"
    )
    await azure_ai_inference_service.generate_embeddings(texts, settings)

    mock_embed.assert_awaited_once_with(
        input=texts,
        model=model_id,
        model_extras=None,
        dimensions=settings.dimensions,
        encoding_format=settings.encoding_format,
        input_type=settings.input_type,
    )


@pytest.mark.parametrize(
    "azure_ai_inference_service",
    [AzureAIInferenceTextEmbedding.__name__],
    indirect=True,
)
@patch.object(EmbeddingsClient, "embed", new_callable=AsyncMock)
async def test_azure_ai_inference_text_embedding_with_extra_parameters(
    mock_embed,
    azure_ai_inference_service,
    model_id,
) -> None:
    """Test text embedding generation of AzureAIInferenceTextEmbedding with extra parameters"""
    texts = ["hello", "world"]
    extra_parameters = {"test_key": "test_value"}
    settings = AzureAIInferenceEmbeddingPromptExecutionSettings(extra_parameters=extra_parameters)
    await azure_ai_inference_service.generate_embeddings(texts, settings)

    mock_embed.assert_awaited_once_with(
        input=texts,
        model=model_id,
        model_extras=extra_parameters,
        dimensions=settings.dimensions,
        encoding_format=settings.encoding_format,
        input_type=settings.input_type,
    )
