# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from ollama import AsyncClient

from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.ollama.ollama_prompt_execution_settings import OllamaChatPromptExecutionSettings
from semantic_kernel.connectors.ai.ollama.services.ollama_chat_completion import OllamaChatCompletion
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.exceptions.service_exceptions import (
    ServiceInitializationError,
    ServiceInvalidExecutionSettingsError,
    ServiceInvalidResponseError,
)


def test_settings(model_id):
    """Test that the settings class is correct."""
    ollama = OllamaChatCompletion(ai_model_id=model_id)
    settings = ollama.get_prompt_execution_settings_class()
    assert settings == OllamaChatPromptExecutionSettings


def test_init_empty_service_id(model_id):
    """Test that the service initializes correctly with an empty service id."""
    ollama = OllamaChatCompletion(ai_model_id=model_id)
    assert ollama.service_id == model_id


def test_init_empty_string_ai_model_id():
    """Test that the service initializes with a error if there is no ai_model_id."""
    with pytest.raises(ServiceInitializationError):
        _ = OllamaChatCompletion(ai_model_id="")


def test_custom_client(model_id, custom_client):
    """Test that the service initializes correctly with a custom client."""
    ollama = OllamaChatCompletion(ai_model_id=model_id, client=custom_client)
    assert ollama.client == custom_client


def test_invalid_ollama_settings():
    """Test that the service initializes incorrectly with invalid settings."""
    with pytest.raises(ServiceInitializationError):
        _ = OllamaChatCompletion(ai_model_id=123)


@pytest.mark.parametrize("exclude_list", [["OLLAMA_CHAT_MODEL_ID"]], indirect=True)
def test_init_empty_model_id_in_env(ollama_unit_test_env):
    """Test that the service initializes incorrectly with an empty model id."""
    with pytest.raises(ServiceInitializationError):
        _ = OllamaChatCompletion(env_file_path="fake_env_file_path.env")


def test_function_choice_settings(ollama_unit_test_env):
    """Test that REQUIRED and NONE function choice settings are unsupported."""
    ollama = OllamaChatCompletion()
    with pytest.raises(ServiceInvalidExecutionSettingsError):
        ollama._verify_function_choice_settings(
            OllamaChatPromptExecutionSettings(function_choice_behavior=FunctionChoiceBehavior.Required())
        )

    with pytest.raises(ServiceInvalidExecutionSettingsError):
        ollama._verify_function_choice_settings(
            OllamaChatPromptExecutionSettings(function_choice_behavior=FunctionChoiceBehavior.NoneInvoke())
        )


def test_service_url(ollama_unit_test_env):
    """Test that the service URL is correct."""
    ollama = OllamaChatCompletion()
    assert ollama.service_url() == ollama_unit_test_env["OLLAMA_HOST"]


@patch("ollama.AsyncClient.__init__", return_value=None)  # mock_client
@patch("ollama.AsyncClient.chat")  # mock_chat_client
async def test_custom_host(
    mock_chat_client,
    mock_client,
    model_id,
    service_id,
    host,
    chat_history,
    prompt,
    default_options,
):
    """Test that the service initializes and generates content correctly with a custom host."""
    mock_chat_client.return_value = {"message": {"content": "test_response"}}

    ollama = OllamaChatCompletion(ai_model_id=model_id, host=host)

    chat_responses = await ollama.get_chat_message_contents(
        chat_history,
        OllamaChatPromptExecutionSettings(service_id=service_id, options=default_options),
    )

    # Check that the client was initialized once with the correct host
    assert mock_client.call_count == 1
    mock_client.assert_called_with(host=host)
    # Check that the chat client was called once and the responses are correct
    assert mock_chat_client.call_count == 1
    assert len(chat_responses) == 1
    assert chat_responses[0].content == "test_response"


@patch("ollama.AsyncClient.__init__", return_value=None)  # mock_client
@patch("ollama.AsyncClient.chat")  # mock_chat_client
async def test_custom_host_streaming(
    mock_chat_client,
    mock_client,
    mock_streaming_chat_response,
    model_id,
    service_id,
    host,
    chat_history,
    prompt,
    default_options,
):
    """Test that the service initializes and generates streaming content correctly with a custom host."""
    mock_chat_client.return_value = mock_streaming_chat_response

    ollama = OllamaChatCompletion(ai_model_id=model_id, host=host)

    async for messages in ollama.get_streaming_chat_message_contents(
        chat_history,
        OllamaChatPromptExecutionSettings(service_id=service_id, options=default_options),
    ):
        assert len(messages) == 1
        assert messages[0].role == "assistant"
        assert messages[0].content == "test_response"

    # Check that the client was initialized once with the correct host
    assert mock_client.call_count == 1
    mock_client.assert_called_with(host=host)
    # Check that the chat client was called once
    assert mock_chat_client.call_count == 1


@patch("ollama.AsyncClient.chat")
async def test_chat_completion(mock_chat_client, model_id, service_id, chat_history, default_options):
    """Test that the chat completion service completes correctly."""
    mock_chat_client.return_value = {"message": {"content": "test_response"}}

    ollama = OllamaChatCompletion(ai_model_id=model_id)
    response = await ollama.get_chat_message_contents(
        chat_history=chat_history,
        settings=OllamaChatPromptExecutionSettings(service_id=service_id, options=default_options),
    )

    assert len(response) == 1
    assert response[0].content == "test_response"
    mock_chat_client.assert_called_once_with(
        model=model_id,
        messages=ollama._prepare_chat_history_for_request(chat_history),
        options=default_options,
        stream=False,
    )


@patch("ollama.AsyncClient.chat")
async def test_chat_completion_wrong_return_type(
    mock_chat_client,
    mock_streaming_chat_response,
    model_id,
    service_id,
    chat_history,
    default_options,
):
    """Test that the chat completion service fails when the return type is incorrect."""
    mock_chat_client.return_value = mock_streaming_chat_response  # should not be a streaming response

    ollama = OllamaChatCompletion(ai_model_id=model_id)
    with pytest.raises(ServiceInvalidResponseError):
        await ollama.get_chat_message_contents(
            chat_history,
            OllamaChatPromptExecutionSettings(service_id=service_id, options=default_options),
        )


@patch("ollama.AsyncClient.chat")
async def test_streaming_chat_completion(
    mock_chat_client,
    mock_streaming_chat_response,
    model_id,
    service_id,
    chat_history,
    default_options,
):
    """Test that the streaming chat completion service completes correctly."""
    mock_chat_client.return_value = mock_streaming_chat_response

    ollama = OllamaChatCompletion(ai_model_id=model_id)
    response = ollama.get_streaming_chat_message_contents(
        chat_history,
        OllamaChatPromptExecutionSettings(service_id=service_id, options=default_options),
    )

    responses = []
    async for line in response:
        if line:
            assert line[0].content == "test_response"
            responses.append(line[0].content)
    assert len(responses) == 1

    mock_chat_client.assert_called_once_with(
        model=model_id,
        messages=ollama._prepare_chat_history_for_request(chat_history),
        options=default_options,
        stream=True,
    )


@patch("ollama.AsyncClient.chat")
async def test_streaming_chat_completion_wrong_return_type(
    mock_chat_client,
    model_id,
    service_id,
    chat_history,
    default_options,
):
    """Test that the chat completion streaming service fails when the return type is incorrect."""
    mock_chat_client.return_value = {"message": {"content": "test_response"}}  # should not be a non-streaming response

    ollama = OllamaChatCompletion(ai_model_id=model_id)
    with pytest.raises(ServiceInvalidResponseError):
        async for _ in ollama.get_streaming_chat_message_contents(
            chat_history,
            OllamaChatPromptExecutionSettings(service_id=service_id, options=default_options),
        ):
            pass


@pytest.fixture
async def setup_ollama_chat_completion():
    async_client_mock = AsyncMock(spec=AsyncClient)
    async_client_mock.chat = AsyncMock()
    ollama_chat_completion = OllamaChatCompletion(
        service_id="test_service", ai_model_id="test_model_id", client=async_client_mock
    )
    return ollama_chat_completion, async_client_mock


async def test_service_url_new(setup_ollama_chat_completion):
    ollama_chat_completion, async_client_mock = setup_ollama_chat_completion
    # Mock the client's internal structure
    async_client_mock._client = AsyncMock(spec=httpx.AsyncClient)
    async_client_mock._client.base_url = "http://mocked_base_url"

    service_url = ollama_chat_completion.service_url()
    assert service_url == "http://mocked_base_url"


async def test_prepare_chat_history_for_request(setup_ollama_chat_completion):
    ollama_chat_completion, _ = setup_ollama_chat_completion
    chat_history = MagicMock(spec=ChatHistory)
    chat_history.messages = []

    prepared_history = ollama_chat_completion._prepare_chat_history_for_request(chat_history)
    assert prepared_history == []
