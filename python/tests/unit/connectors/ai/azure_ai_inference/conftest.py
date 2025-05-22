# Copyright (c) Microsoft. All rights reserved.

import datetime
from collections.abc import AsyncGenerator, AsyncIterator
from unittest.mock import MagicMock

import pytest
from azure.ai.inference.aio import ChatCompletionsClient, EmbeddingsClient
from azure.ai.inference.models import (
    ChatChoice,
    ChatCompletions,
    ChatCompletionsToolCall,
    ChatResponseMessage,
    CompletionsUsage,
    FunctionCall,
    StreamingChatChoiceUpdate,
    StreamingChatCompletionsUpdate,
    StreamingChatResponseToolCallUpdate,
)
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


@pytest.fixture()
def model_diagnostics_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for Azure AI Inference Unit Tests."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {
        "SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS": "true",
        "SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS_SENSITIVE": "true",
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


@pytest.fixture()
def mock_azure_ai_inference_chat_completion_response(model_id) -> ChatCompletions:
    return ChatCompletions(
        id="test_id",
        created=datetime.datetime.now(),
        model=model_id,
        usage=CompletionsUsage(
            completion_tokens=0,
            prompt_tokens=0,
            total_tokens=0,
        ),
        choices=[
            ChatChoice(
                index=0,
                finish_reason="stop",
                message=ChatResponseMessage(
                    role="assistant",
                    content="Hello",
                ),
            )
        ],
    )


@pytest.fixture()
def mock_azure_ai_inference_chat_completion_response_with_tool_call(model_id) -> ChatCompletions:
    return ChatCompletions(
        id="test_id",
        created=datetime.datetime.now(),
        model=model_id,
        usage=CompletionsUsage(
            completion_tokens=0,
            prompt_tokens=0,
            total_tokens=0,
        ),
        choices=[
            ChatChoice(
                index=0,
                finish_reason="tool_calls",
                message=ChatResponseMessage(
                    role="assistant",
                    tool_calls=[
                        ChatCompletionsToolCall(
                            id="test_id",
                            function=FunctionCall(
                                name="test_function",
                                arguments={"test_arg": "test_value"},
                            ),
                        ),
                    ],
                ),
            )
        ],
    )


@pytest.fixture()
def mock_azure_ai_inference_streaming_chat_completion_response(model_id) -> AsyncIterator:
    streaming_chat_response = MagicMock(spec=AsyncGenerator)
    streaming_chat_response.__aiter__.return_value = [
        StreamingChatCompletionsUpdate(
            id="test_id",
            created=datetime.datetime.now(),
            model=model_id,
            usage=CompletionsUsage(
                completion_tokens=0,
                prompt_tokens=0,
                total_tokens=0,
            ),
            choices=[
                # Empty choice
            ],
        ),
        StreamingChatCompletionsUpdate(
            id="test_id",
            created=datetime.datetime.now(),
            model=model_id,
            usage=CompletionsUsage(
                completion_tokens=0,
                prompt_tokens=0,
                total_tokens=0,
            ),
            choices=[
                StreamingChatChoiceUpdate(
                    index=0,
                    finish_reason="stop",
                    delta=ChatResponseMessage(
                        role="assistant",
                        content="Hello",
                    ),
                )
            ],
        ),
    ]

    return streaming_chat_response


@pytest.fixture()
def mock_azure_ai_inference_streaming_chat_completion_response_with_tool_call(model_id) -> AsyncIterator:
    streaming_chat_response = MagicMock(spec=AsyncGenerator)
    streaming_chat_response.__aiter__.return_value = [
        StreamingChatCompletionsUpdate(
            id="test_id",
            created=datetime.datetime.now(),
            model=model_id,
            usage=CompletionsUsage(
                completion_tokens=0,
                prompt_tokens=0,
                total_tokens=0,
            ),
            choices=[
                # Empty choice
            ],
        ),
        StreamingChatCompletionsUpdate(
            id="test_id",
            created=datetime.datetime.now(),
            model=model_id,
            usage=CompletionsUsage(
                completion_tokens=0,
                prompt_tokens=0,
                total_tokens=0,
            ),
            choices=[
                StreamingChatChoiceUpdate(
                    index=0,
                    finish_reason="tool_calls",
                    delta=ChatResponseMessage(
                        role="assistant",
                        tool_calls=[
                            StreamingChatResponseToolCallUpdate(
                                id="test_id",
                                function=FunctionCall(
                                    name="getLightStatus",
                                    arguments={"arg1": "test_value"},
                                ),
                            ),
                        ],
                    ),
                )
            ],
        ),
    ]

    return streaming_chat_response
