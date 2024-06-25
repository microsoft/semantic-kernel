# Copyright (c) Microsoft. All rights reserved.

import pytest
from azure.ai.inference.aio import ChatCompletionsClient, EmbeddingsClient
from azure.core.credentials import AzureKeyCredential

from semantic_kernel.connectors.ai.azure_ai_inference import (
    AzureAIInferenceChatCompletion,
    AzureAIInferenceTextEmbedding,
)


@pytest.fixture()
def model_id() -> str:
    return "test_model_id"


@pytest.fixture()
def service_id() -> str:
    return "test_service_id"


@pytest.fixture()
def azure_ai_inference_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for Azure AI Inference Unit Tests."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {
        "AZURE_AI_INFERENCE_API_KEY": "test-api-key",
        "AZURE_AI_INFERENCE_ENDPOINT": "https://test-endpoint.com",
    }

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@pytest.fixture(scope="function")
def azure_ai_inference_client(azure_ai_inference_unit_test_env, request) -> ChatCompletionsClient | EmbeddingsClient:
    """Fixture to create Azure AI Inference client for unit tests."""
    endpoint = azure_ai_inference_unit_test_env["AZURE_AI_INFERENCE_ENDPOINT"]
    api_key = azure_ai_inference_unit_test_env["AZURE_AI_INFERENCE_API_KEY"]
    credential = AzureKeyCredential(api_key)

    if request.param == AzureAIInferenceChatCompletion.__name__:
        return ChatCompletionsClient(endpoint=endpoint, credential=credential)
    if request.param == AzureAIInferenceTextEmbedding.__name__:
        return EmbeddingsClient(endpoint=endpoint, credential=credential)

    raise ValueError(f"Service {request.param} not supported.")


@pytest.fixture(scope="function")
def azure_ai_inference_service(azure_ai_inference_unit_test_env, model_id, request):
    """Fixture to create Azure AI Inference service for unit tests.

    This is required because the Azure AI Inference services require a client to be created,
    and the client will be talking to the endpoint at creation time.
    """

    endpoint = azure_ai_inference_unit_test_env["AZURE_AI_INFERENCE_ENDPOINT"]
    api_key = azure_ai_inference_unit_test_env["AZURE_AI_INFERENCE_API_KEY"]

    if request.param == AzureAIInferenceChatCompletion.__name__:
        return AzureAIInferenceChatCompletion(model_id, api_key=api_key, endpoint=endpoint)
    if request.param == AzureAIInferenceTextEmbedding.__name__:
        return AzureAIInferenceTextEmbedding(model_id, api_key=api_key, endpoint=endpoint)

    raise ValueError(f"Service {request.param} not supported.")
