# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch

import pytest
from azure.ai.inference.aio import EmbeddingsClient
from azure.ai.inference.models import ModelInfo, ModelType
from azure.core.credentials import AzureKeyCredential

from semantic_kernel.connectors.ai.azure_ai_inference.azure_ai_inference_prompt_execution_settings import (
    AzureAIInferenceEmbeddingPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.azure_ai_inference.services.azure_ai_inference_text_embedding import (
    AzureAIInferenceTextEmbedding,
)
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError


@patch.object(AzureAIInferenceTextEmbedding, "_create_client")
def test_azure_ai_inference_text_embedding_init(
    mock_create_client,
    azure_ai_inference_unit_test_env,
) -> None:
    """Test initialization of AzureAIInferenceChatCompletion"""
    mock_client = EmbeddingsClient(
        endpoint=azure_ai_inference_unit_test_env["AZURE_AI_INFERENCE_ENDPOINT"],
        credential=AzureKeyCredential(
            azure_ai_inference_unit_test_env["AZURE_AI_INFERENCE_API_KEY"]
        ),
    )
    mock_model_info = ModelInfo(
        model_name="test_model_id",
        model_type=ModelType.EMBEDDINGS,
    )
    mock_create_client.return_value = (mock_client, mock_model_info)

    azure_ai_inference = AzureAIInferenceTextEmbedding()

    assert azure_ai_inference.ai_model_id == "test_model_id"
    assert azure_ai_inference.service_id == "test_model_id"
    assert isinstance(azure_ai_inference.client, EmbeddingsClient)


@pytest.mark.parametrize(
    "exclude_list", [["AZURE_AI_INFERENCE_API_KEY"]], indirect=True
)
def test_azure_ai_inference_text_embedding_init_with_empty_api_key(
    azure_ai_inference_unit_test_env,
) -> None:
    """Test initialization of AzureAIInferenceChatCompletion with empty API key"""
    with pytest.raises(ServiceInitializationError):
        AzureAIInferenceTextEmbedding()


@pytest.mark.parametrize(
    "exclude_list", [["AZURE_AI_INFERENCE_ENDPOINT"]], indirect=True
)
def test_azure_ai_inference_text_embedding_init_with_empty_endpoint_and_base_url(
    azure_ai_inference_unit_test_env,
) -> None:
    """Test initialization of AzureAIInferenceChatCompletion with empty endpoint and base url"""
    with pytest.raises(ServiceInitializationError):
        AzureAIInferenceTextEmbedding()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "azure_ai_inference_service",
    [AzureAIInferenceTextEmbedding.__name__],
    indirect=True,
)
@patch.object(EmbeddingsClient, "embed", new_callable=AsyncMock)
async def test_azure_ai_inference_text_embedding(
    mock_embed,
    azure_ai_inference_service,
) -> None:
    """Test text embedding generation of AzureAIInferenceTextEmbedding without settings"""
    texts = ["hello", "world"]
    await azure_ai_inference_service.generate_embeddings(texts)

    mock_embed.assert_awaited_once_with(
        input=texts,
        model_extras=None,
        dimensions=None,
        encoding_format=None,
        input_type=None,
        kwargs={},
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "azure_ai_inference_service",
    [AzureAIInferenceTextEmbedding.__name__],
    indirect=True,
)
@patch.object(EmbeddingsClient, "embed", new_callable=AsyncMock)
async def test_azure_ai_inference_text_embedding_with_standard_settings(
    mock_embed,
    azure_ai_inference_service,
) -> None:
    """Test text embedding generation of AzureAIInferenceTextEmbedding with standard settings"""
    texts = ["hello", "world"]
    settings = AzureAIInferenceEmbeddingPromptExecutionSettings()
    await azure_ai_inference_service.generate_embeddings(texts, settings=settings)

    mock_embed.assert_awaited_once_with(
        input=texts,
        model_extras=None,
        dimensions=settings.dimensions,
        encoding_format=settings.encoding_format,
        input_type=settings.input_type,
        kwargs={"settings": settings},
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "azure_ai_inference_service",
    [AzureAIInferenceTextEmbedding.__name__],
    indirect=True,
)
@patch.object(EmbeddingsClient, "embed", new_callable=AsyncMock)
async def test_azure_ai_inference_text_embedding_with_extra_parameters(
    mock_embed,
    azure_ai_inference_service,
) -> None:
    """Test text embedding generation of AzureAIInferenceTextEmbedding with extra parameters"""
    texts = ["hello", "world"]
    extra_parameters = {"test_key": "test_value"}
    settings = AzureAIInferenceEmbeddingPromptExecutionSettings(
        extra_parameters=extra_parameters
    )
    await azure_ai_inference_service.generate_embeddings(texts, settings=settings)

    mock_embed.assert_awaited_once_with(
        input=texts,
        model_extras=extra_parameters,
        dimensions=settings.dimensions,
        encoding_format=settings.encoding_format,
        input_type=settings.input_type,
        kwargs={"settings": settings},
    )
