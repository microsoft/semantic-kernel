# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import patch

import pytest
from azure.ai.inference.aio import ChatCompletionsClient
from azure.ai.inference.models import ModelInfo, ModelType
from azure.core.credentials import AzureKeyCredential

from semantic_kernel.connectors.ai.azure_ai_inference.services.azure_ai_inference_chat_completion import (
    AzureAIInferenceChatCompletion,
)
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError


@patch.object(AzureAIInferenceChatCompletion, "_create_client")
def test_azure_ai_inference_chat_completion_init(
    mock_create_client,
    azure_ai_inference_unit_test_env,
) -> None:
    """Test initialization of AzureAIInferenceChatCompletion"""
    mock_client = ChatCompletionsClient(
        endpoint=azure_ai_inference_unit_test_env["AZURE_AI_INFERENCE_ENDPOINT"],
        credential=AzureKeyCredential(
            azure_ai_inference_unit_test_env["AZURE_AI_INFERENCE_API_KEY"]
        ),
    )
    mock_model_info = ModelInfo(
        model_name="test_model_id",
        model_type=ModelType.CHAT,
    )
    mock_create_client.return_value = (mock_client, mock_model_info)

    azure_ai_inference = AzureAIInferenceChatCompletion()

    assert isinstance(azure_ai_inference, AzureAIInferenceChatCompletion)
    assert azure_ai_inference.ai_model_id == "test_model_id"
    assert azure_ai_inference.service_id == "test_model_id"
    assert isinstance(azure_ai_inference.client, ChatCompletionsClient)


@pytest.mark.parametrize(
    "exclude_list", [["AZURE_AI_INFERENCE_API_KEY"]], indirect=True
)
def test_azure_chat_completion_init_with_empty_api_key(
    azure_ai_inference_unit_test_env,
) -> None:
    """Test initialization of AzureAIInferenceChatCompletion with empty API key"""
    with pytest.raises(ServiceInitializationError):
        AzureAIInferenceChatCompletion()


@pytest.mark.parametrize(
    "exclude_list", [["AZURE_AI_INFERENCE_ENDPOINT"]], indirect=True
)
def test_azure_chat_completion_init_with_empty_endpoint_and_base_url(
    azure_ai_inference_unit_test_env,
) -> None:
    """Test initialization of AzureAIInferenceChatCompletion with empty endpoint and base url"""
    with pytest.raises(ServiceInitializationError):
        AzureAIInferenceChatCompletion()
