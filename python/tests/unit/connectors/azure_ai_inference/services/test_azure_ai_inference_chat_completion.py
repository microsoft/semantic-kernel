# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch

import pytest
from azure.ai.inference.aio import ChatCompletionsClient
from azure.ai.inference.models import UserMessage

from semantic_kernel.connectors.ai.azure_ai_inference import (
    AzureAIInferenceChatCompletion,
    AzureAIInferenceChatPromptExecutionSettings,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError


def test_azure_ai_inference_chat_completion_init(azure_ai_inference_unit_test_env, model_id) -> None:
    azure_ai_inference = AzureAIInferenceChatCompletion(model_id)

    assert azure_ai_inference.ai_model_id == model_id
    assert azure_ai_inference.service_id == model_id
    assert isinstance(azure_ai_inference.client, ChatCompletionsClient)


def test_azure_ai_inference_chat_completion_init_with_service_id(
    azure_ai_inference_unit_test_env, model_id, service_id
) -> None:
    azure_ai_inference = AzureAIInferenceChatCompletion(model_id, service_id=service_id)

    assert azure_ai_inference.ai_model_id == model_id
    assert azure_ai_inference.service_id == service_id
    assert isinstance(azure_ai_inference.client, ChatCompletionsClient)


@pytest.mark.parametrize(
    "azure_ai_inference_client",
    [AzureAIInferenceChatCompletion.__name__],
    indirect=True,
)
def test_azure_ai_inference_chat_completion_init_with_custom_client(azure_ai_inference_client, model_id) -> None:
    """Test initialization of AzureAIInferenceChatCompletion with custom client"""
    client = azure_ai_inference_client
    azure_ai_inference = AzureAIInferenceChatCompletion(model_id, client=client)

    assert azure_ai_inference.ai_model_id == model_id
    assert azure_ai_inference.service_id == model_id
    assert azure_ai_inference.client == client


@pytest.mark.parametrize("exclude_list", [["AZURE_AI_INFERENCE_API_KEY"]], indirect=True)
def test_azure_ai_inference_chat_completion_init_with_empty_api_key(azure_ai_inference_unit_test_env, model_id) -> None:
    """Test initialization of AzureAIInferenceChatCompletion with empty API key"""
    with pytest.raises(ServiceInitializationError):
        AzureAIInferenceChatCompletion(model_id)


@pytest.mark.parametrize("exclude_list", [["AZURE_AI_INFERENCE_ENDPOINT"]], indirect=True)
def test_azure_ai_inference_chat_completion_init_with_empty_endpoint(
    azure_ai_inference_unit_test_env, model_id
) -> None:
    """Test initialization of AzureAIInferenceChatCompletion with empty endpoint"""
    with pytest.raises(ServiceInitializationError):
        AzureAIInferenceChatCompletion(model_id)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "azure_ai_inference_service",
    [AzureAIInferenceChatCompletion.__name__],
    indirect=True,
)
@patch.object(ChatCompletionsClient, "complete", new_callable=AsyncMock)
async def test_azure_ai_inference_chat_completion(
    mock_complete,
    azure_ai_inference_service,
    chat_history: ChatHistory,
) -> None:
    """Test completion of AzureAIInferenceChatCompletion"""
    user_message_content: str = "Hello"
    chat_history.add_user_message(user_message_content)
    settings = AzureAIInferenceChatPromptExecutionSettings()

    await azure_ai_inference_service.get_chat_message_contents(chat_history, settings)

    mock_complete.assert_awaited_once_with(
        messages=[UserMessage(content=user_message_content)],
        model_extras=None,
        **settings.prepare_settings_dict(),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "azure_ai_inference_service",
    [AzureAIInferenceChatCompletion.__name__],
    indirect=True,
)
@patch.object(ChatCompletionsClient, "complete", new_callable=AsyncMock)
async def test_azure_ai_inference_chat_completion_with_standard_parameters(
    mock_complete,
    azure_ai_inference_service,
    chat_history: ChatHistory,
) -> None:
    """Test completion of AzureAIInferenceChatCompletion with standard OpenAI parameters"""
    user_message_content: str = "Hello"
    chat_history.add_user_message(user_message_content)

    settings = AzureAIInferenceChatPromptExecutionSettings(
        frequency_penalty=0.5,
        max_tokens=100,
        presence_penalty=0.5,
        seed=123,
        stop="stop",
        temperature=0.5,
        top_p=0.5,
    )

    await azure_ai_inference_service.get_chat_message_contents(chat_history, settings)

    mock_complete.assert_awaited_once_with(
        messages=[UserMessage(content=user_message_content)],
        model_extras=None,
        frequency_penalty=settings.frequency_penalty,
        max_tokens=settings.max_tokens,
        presence_penalty=settings.presence_penalty,
        seed=settings.seed,
        stop=settings.stop,
        temperature=settings.temperature,
        top_p=settings.top_p,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "azure_ai_inference_service",
    [AzureAIInferenceChatCompletion.__name__],
    indirect=True,
)
@patch.object(ChatCompletionsClient, "complete", new_callable=AsyncMock)
async def test_azure_ai_inference_chat_completion_with_extra_parameters(
    mock_complete,
    azure_ai_inference_service,
    chat_history: ChatHistory,
) -> None:
    """Test completion of AzureAIInferenceChatCompletion with extra parameters"""
    user_message_content: str = "Hello"
    chat_history.add_user_message(user_message_content)
    extra_parameters = {"test_key": "test_value"}

    settings = AzureAIInferenceChatPromptExecutionSettings(extra_parameters=extra_parameters)

    await azure_ai_inference_service.get_chat_message_contents(chat_history, settings)

    mock_complete.assert_awaited_once_with(
        messages=[UserMessage(content=user_message_content)],
        model_extras=extra_parameters,
        **settings.prepare_settings_dict(),
    )
