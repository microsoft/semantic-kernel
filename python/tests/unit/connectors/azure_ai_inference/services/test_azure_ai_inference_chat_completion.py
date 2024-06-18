# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch

import pytest
from azure.ai.inference.aio import ChatCompletionsClient
from azure.ai.inference.models import ModelInfo, ModelType, UserMessage
from azure.core.credentials import AzureKeyCredential

from semantic_kernel.connectors.ai.azure_ai_inference import (
    AzureAIInferenceChatCompletion,
    AzureAIInferenceChatPromptExecutionSettings,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError


@patch.object(AzureAIInferenceChatCompletion, "_create_client")
def test_azure_ai_inference_chat_completion_init(
    mock_create_client,
    azure_ai_inference_unit_test_env,
) -> None:
    """Test initialization of AzureAIInferenceChatCompletion"""
    mock_client = ChatCompletionsClient(
        endpoint=azure_ai_inference_unit_test_env["AZURE_AI_INFERENCE_ENDPOINT"],
        credential=AzureKeyCredential(azure_ai_inference_unit_test_env["AZURE_AI_INFERENCE_API_KEY"]),
    )
    mock_model_info = ModelInfo(
        model_name="test_model_id",
        model_type=ModelType.CHAT,
    )
    mock_create_client.return_value = (mock_client, mock_model_info)

    azure_ai_inference = AzureAIInferenceChatCompletion()

    assert azure_ai_inference.ai_model_id == "test_model_id"
    assert azure_ai_inference.service_id == "test_model_id"
    assert isinstance(azure_ai_inference.client, ChatCompletionsClient)


@pytest.mark.parametrize(
    "azure_ai_inference_client",
    [AzureAIInferenceChatCompletion.__name__],
    indirect=True,
)
def test_azure_ai_inference_chat_completion_init_with_custom_client(
    azure_ai_inference_client,
) -> None:
    """Test initialization of AzureAIInferenceChatCompletion with custom client"""
    client, model_info = azure_ai_inference_client
    azure_ai_inference = AzureAIInferenceChatCompletion(client=client, model_info=model_info)

    assert azure_ai_inference.ai_model_id == model_info.model_name
    assert azure_ai_inference.service_id == model_info.model_name
    assert azure_ai_inference.client == client


@pytest.mark.parametrize("exclude_list", [["AZURE_AI_INFERENCE_API_KEY"]], indirect=True)
def test_azure_ai_inference_chat_completion_init_with_empty_api_key(
    azure_ai_inference_unit_test_env,
) -> None:
    """Test initialization of AzureAIInferenceChatCompletion with empty API key"""
    with pytest.raises(ServiceInitializationError):
        AzureAIInferenceChatCompletion()


@pytest.mark.parametrize("exclude_list", [["AZURE_AI_INFERENCE_ENDPOINT"]], indirect=True)
def test_azure_ai_inference_chat_completion_init_with_empty_endpoint_and_base_url(
    azure_ai_inference_unit_test_env,
) -> None:
    """Test initialization of AzureAIInferenceChatCompletion with empty endpoint and base url"""
    with pytest.raises(ServiceInitializationError):
        AzureAIInferenceChatCompletion()


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
