# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from ollama import AsyncClient, ChatResponse, Message

from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.ollama.ollama_prompt_execution_settings import OllamaChatPromptExecutionSettings
from semantic_kernel.connectors.ai.ollama.services.ollama_chat_completion import OllamaChatCompletion
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
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
async def ollama_chat_completion(model_id):
    with patch(
        "ollama.AsyncClient",
        spec=AsyncClient,
    ) as mock_client:
        mock_client.return_value = AsyncMock(spec=AsyncClient)
        yield OllamaChatCompletion(client=mock_client, ai_model_id=model_id)


def test_initialization_failure():
    """Test initialization with missing chat model id raises an error."""
    with patch(
        "semantic_kernel.connectors.ai.ollama.ollama_settings.OllamaSettings.create",
        side_effect=ServiceInitializationError,
    ) as mock_create:
        with pytest.raises(ServiceInitializationError):
            OllamaChatCompletion(ai_model_id=None)

        mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_service_url_returns_default_value_without_client(
    model_id,
):
    """Test the service_url method returns default value when client has no base_url."""
    chat_service = OllamaChatCompletion(ai_model_id=model_id, client=None)
    assert chat_service.service_url() == "http://127.0.0.1:11434"


@pytest.mark.asyncio
async def test_get_prompt_execution_settings_class(ollama_chat_completion):
    """Test getting the correct prompt execution settings class."""
    assert ollama_chat_completion.get_prompt_execution_settings_class() is OllamaChatPromptExecutionSettings


@pytest.mark.asyncio
async def test_inner_get_chat_message_contents_valid(ollama_chat_completion):
    """Test _inner_get_chat_message_contents with valid response."""
    valid_message = Message(content="Valid content", role="user")
    valid_response = ChatResponse(message=valid_message)
    ollama_chat_completion.client.chat = AsyncMock(return_value=valid_response)

    chat_history = ChatHistory(messages=[])
    settings = OllamaChatPromptExecutionSettings()

    result = await ollama_chat_completion._inner_get_chat_message_contents(chat_history, settings)

    assert len(result) == 1
    assert isinstance(result[0], ChatMessageContent)
    assert result[0].items[0].text == "Valid content"


@pytest.mark.asyncio
async def test_inner_get_chat_message_contents_invalid_response(ollama_chat_completion):
    """Test _inner_get_chat_message_contents raises error on invalid response types."""
    invalid_response = MagicMock()
    invalid_response.message.content = None
    ollama_chat_completion.client.chat.return_value = invalid_response

    chat_history = ChatHistory(messages=[])
    settings = OllamaChatPromptExecutionSettings()

    with pytest.raises(ServiceInvalidResponseError):
        await ollama_chat_completion._inner_get_chat_message_contents(chat_history, settings)
