# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch

import pytest
from azure.ai.inference.aio import ChatCompletionsClient

from semantic_kernel.connectors.ai.azure_ai_inference.azure_ai_inference_prompt_execution_settings import (
    AzureAIInferenceChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.azure_ai_inference.services.azure_ai_inference_chat_completion import (
    AzureAIInferenceChatCompletion,
)
from semantic_kernel.contents.chat_history import ChatHistory


@pytest.mark.parametrize(
    "azure_ai_inference_service",
    [AzureAIInferenceChatCompletion.__name__],
    indirect=True,
)
@patch.object(ChatCompletionsClient, "complete", new_callable=AsyncMock)
@patch("azure.ai.inference.tracing.AIInferenceInstrumentor.uninstrument")
@patch("azure.ai.inference.tracing.AIInferenceInstrumentor.instrument")
async def test_azure_ai_inference_chat_completion_instrumentation(
    mock_instrument,
    mock_uninstrument,
    mock_complete,
    azure_ai_inference_service,
    chat_history: ChatHistory,
    mock_azure_ai_inference_chat_completion_response,
    model_diagnostics_test_env,
) -> None:
    """Test completion of AzureAIInferenceChatCompletion"""
    settings = AzureAIInferenceChatPromptExecutionSettings()

    mock_complete.return_value = mock_azure_ai_inference_chat_completion_response

    await azure_ai_inference_service.get_chat_message_contents(chat_history=chat_history, settings=settings)

    mock_instrument.assert_called_once_with(enable_content_recording=True)
    mock_uninstrument.assert_called_once()


@pytest.mark.parametrize(
    "azure_ai_inference_service",
    [
        AzureAIInferenceChatCompletion.__name__,
    ],
    indirect=True,
)
@pytest.mark.parametrize(
    "override_env_param_dict",
    [
        {
            "SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS": "False",
            "SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS_SENSITIVE": "False",
        },
    ],
    indirect=True,
)
@patch.object(ChatCompletionsClient, "complete", new_callable=AsyncMock)
@patch("azure.ai.inference.tracing.AIInferenceInstrumentor.uninstrument")
@patch("azure.ai.inference.tracing.AIInferenceInstrumentor.instrument")
async def test_azure_ai_inference_chat_completion_not_instrumentation(
    mock_instrument,
    mock_uninstrument,
    mock_complete,
    azure_ai_inference_service,
    chat_history: ChatHistory,
    mock_azure_ai_inference_chat_completion_response,
    model_diagnostics_test_env,
) -> None:
    """Test completion of AzureAIInferenceChatCompletion"""
    settings = AzureAIInferenceChatPromptExecutionSettings()

    mock_complete.return_value = mock_azure_ai_inference_chat_completion_response

    await azure_ai_inference_service.get_chat_message_contents(chat_history=chat_history, settings=settings)

    mock_instrument.assert_not_called()
    mock_uninstrument.assert_not_called()


@pytest.mark.parametrize(
    "azure_ai_inference_service",
    [
        AzureAIInferenceChatCompletion.__name__,
    ],
    indirect=True,
)
@pytest.mark.parametrize(
    "override_env_param_dict",
    [
        {
            "SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS": "True",
            "SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS_SENSITIVE": "False",
        },
    ],
    indirect=True,
)
@patch.object(ChatCompletionsClient, "complete", new_callable=AsyncMock)
@patch("azure.ai.inference.tracing.AIInferenceInstrumentor.uninstrument")
@patch("azure.ai.inference.tracing.AIInferenceInstrumentor.instrument")
async def test_azure_ai_inference_chat_completion_instrumentation_without_sensitive(
    mock_instrument,
    mock_uninstrument,
    mock_complete,
    azure_ai_inference_service,
    chat_history: ChatHistory,
    mock_azure_ai_inference_chat_completion_response,
    model_diagnostics_test_env,
) -> None:
    """Test completion of AzureAIInferenceChatCompletion"""
    settings = AzureAIInferenceChatPromptExecutionSettings()

    mock_complete.return_value = mock_azure_ai_inference_chat_completion_response

    await azure_ai_inference_service.get_chat_message_contents(chat_history=chat_history, settings=settings)

    mock_instrument.assert_called_once_with(enable_content_recording=False)
    mock_uninstrument.assert_called_once()


@pytest.mark.parametrize(
    "azure_ai_inference_service",
    [AzureAIInferenceChatCompletion.__name__],
    indirect=True,
)
@patch.object(ChatCompletionsClient, "complete", new_callable=AsyncMock)
@patch("azure.ai.inference.tracing.AIInferenceInstrumentor.uninstrument")
@patch("azure.ai.inference.tracing.AIInferenceInstrumentor.instrument")
async def test_azure_ai_inference_streaming_chat_completion_instrumentation(
    mock_instrument,
    mock_uninstrument,
    mock_complete,
    azure_ai_inference_service,
    chat_history: ChatHistory,
    mock_azure_ai_inference_streaming_chat_completion_response,
    model_diagnostics_test_env,
) -> None:
    """Test completion of AzureAIInferenceChatCompletion"""
    settings = AzureAIInferenceChatPromptExecutionSettings()

    mock_complete.return_value = mock_azure_ai_inference_streaming_chat_completion_response

    async for _ in azure_ai_inference_service.get_streaming_chat_message_contents(
        chat_history=chat_history, settings=settings
    ):
        pass

    mock_instrument.assert_called_once_with(enable_content_recording=True)
    mock_uninstrument.assert_called_once()


@pytest.mark.parametrize(
    "azure_ai_inference_service",
    [
        AzureAIInferenceChatCompletion.__name__,
    ],
    indirect=True,
)
@pytest.mark.parametrize(
    "override_env_param_dict",
    [
        {
            "SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS": "False",
            "SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS_SENSITIVE": "False",
        },
    ],
    indirect=True,
)
@patch.object(ChatCompletionsClient, "complete", new_callable=AsyncMock)
@patch("azure.ai.inference.tracing.AIInferenceInstrumentor.uninstrument")
@patch("azure.ai.inference.tracing.AIInferenceInstrumentor.instrument")
async def test_azure_ai_inference_streaming_chat_completion_not_instrumentation(
    mock_instrument,
    mock_uninstrument,
    mock_complete,
    azure_ai_inference_service,
    chat_history: ChatHistory,
    mock_azure_ai_inference_streaming_chat_completion_response,
    model_diagnostics_test_env,
) -> None:
    """Test completion of AzureAIInferenceChatCompletion"""
    settings = AzureAIInferenceChatPromptExecutionSettings()

    mock_complete.return_value = mock_azure_ai_inference_streaming_chat_completion_response

    async for _ in azure_ai_inference_service.get_streaming_chat_message_contents(
        chat_history=chat_history, settings=settings
    ):
        pass

    mock_instrument.assert_not_called()
    mock_uninstrument.assert_not_called()


@pytest.mark.parametrize(
    "azure_ai_inference_service",
    [
        AzureAIInferenceChatCompletion.__name__,
    ],
    indirect=True,
)
@pytest.mark.parametrize(
    "override_env_param_dict",
    [
        {
            "SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS": "True",
            "SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS_SENSITIVE": "False",
        },
    ],
    indirect=True,
)
@patch.object(ChatCompletionsClient, "complete", new_callable=AsyncMock)
@patch("azure.ai.inference.tracing.AIInferenceInstrumentor.uninstrument")
@patch("azure.ai.inference.tracing.AIInferenceInstrumentor.instrument")
async def test_azure_ai_inference_streaming_chat_completion_instrumentation_without_sensitive(
    mock_instrument,
    mock_uninstrument,
    mock_complete,
    azure_ai_inference_service,
    chat_history: ChatHistory,
    mock_azure_ai_inference_streaming_chat_completion_response,
    model_diagnostics_test_env,
) -> None:
    """Test completion of AzureAIInferenceChatCompletion"""
    settings = AzureAIInferenceChatPromptExecutionSettings()

    mock_complete.return_value = mock_azure_ai_inference_streaming_chat_completion_response

    async for _ in azure_ai_inference_service.get_streaming_chat_message_contents(
        chat_history=chat_history, settings=settings
    ):
        pass

    mock_instrument.assert_called_once_with(enable_content_recording=False)
    mock_uninstrument.assert_called_once()
