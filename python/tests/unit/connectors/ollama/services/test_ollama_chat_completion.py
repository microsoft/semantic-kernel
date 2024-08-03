# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import patch

import pytest

from semantic_kernel.connectors.ai.ollama.ollama_prompt_execution_settings import (
    OllamaChatPromptExecutionSettings,
    OllamaTextPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.ollama.services.ollama_chat_completion import OllamaChatCompletion
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError, ServiceInvalidResponseError


def test_settings(model_id):
    """Test that the settings class is correct."""
    ollama = OllamaChatCompletion(ai_model_id=model_id)
    settings = ollama.get_prompt_execution_settings_class()
    assert settings == OllamaChatPromptExecutionSettings


def test_init_empty_service_id(model_id):
    """Test that the service initializes correctly with an empty service id."""
    ollama = OllamaChatCompletion(ai_model_id=model_id)
    assert ollama.service_id == model_id


def test_custom_client(model_id, custom_client):
    """Test that the service initializes correctly with a custom client."""
    ollama = OllamaChatCompletion(ai_model_id=model_id, client=custom_client)
    assert ollama.client == custom_client


@pytest.mark.parametrize("exclude_list", [["OLLAMA_MODEL"]], indirect=True)
def test_init_empty_model_id(ollama_unit_test_env):
    """Test that the service initializes incorrectly with an empty model id."""
    with pytest.raises(ServiceInitializationError):
        _ = OllamaChatCompletion(env_file_path="fake_env_file_path.env")


@pytest.mark.asyncio
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

    text_responses = await ollama.get_text_contents(
        prompt,
        OllamaTextPromptExecutionSettings(service_id=service_id, options=default_options),
    )

    # Check that the client was initialized once with the correct host
    assert mock_client.call_count == 1
    mock_client.assert_called_with(host=host)
    # Check that the chat client was called twice and the responses are correct
    assert mock_chat_client.call_count == 2
    assert len(chat_responses) == 1
    assert chat_responses[0].content == "test_response"
    assert len(text_responses) == 1
    assert text_responses[0].text == "test_response"


@pytest.mark.asyncio
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

    async for messages in ollama.get_streaming_text_contents(
        prompt,
        OllamaTextPromptExecutionSettings(service_id=service_id, options=default_options),
    ):
        assert len(messages) == 1
        assert messages[0].text == "test_response"

    # Check that the client was initialized once with the correct host
    assert mock_client.call_count == 1
    mock_client.assert_called_with(host=host)
    # Check that the chat client was called twice and the responses are correct
    assert mock_chat_client.call_count == 2


@pytest.mark.asyncio
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


@pytest.mark.asyncio
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


@pytest.mark.asyncio
@patch("ollama.AsyncClient.chat")
async def test_text_completion(mock_chat_client, model_id, service_id, prompt, default_options):
    """Test that the text completion service completes correctly."""
    mock_chat_client.return_value = {"message": {"content": "test_response"}}
    ollama = OllamaChatCompletion(ai_model_id=model_id)
    response = await ollama.get_text_contents(
        prompt=prompt,
        settings=OllamaTextPromptExecutionSettings(service_id=service_id, options=default_options),
    )

    assert len(response) == 1
    assert response[0].text == "test_response"
    mock_chat_client.assert_called_once_with(
        model=model_id,
        messages=[{"role": "user", "content": prompt}],
        options=default_options,
        stream=False,
    )


@pytest.mark.asyncio
@patch("ollama.AsyncClient.chat")
async def test_text_completion_wrong_return_type(
    mock_chat_client,
    mock_streaming_chat_response,
    model_id,
    service_id,
    chat_history,
    default_options,
):
    """Test that the text completion service fails when the return type is incorrect."""
    mock_chat_client.return_value = mock_streaming_chat_response  # should not be a streaming response

    ollama = OllamaChatCompletion(ai_model_id=model_id)
    with pytest.raises(ServiceInvalidResponseError):
        await ollama.get_text_contents(
            chat_history,
            OllamaTextPromptExecutionSettings(service_id=service_id, options=default_options),
        )


@pytest.mark.asyncio
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


@pytest.mark.asyncio
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


@pytest.mark.asyncio
@patch("ollama.AsyncClient.chat")
async def test_streaming_text_completion(
    mock_chat_client,
    mock_streaming_chat_response,
    model_id,
    service_id,
    prompt,
    default_options,
):
    """Test that the streaming text completion service completes correctly."""
    mock_chat_client.return_value = mock_streaming_chat_response

    ollama = OllamaChatCompletion(ai_model_id=model_id)
    response = ollama.get_streaming_text_contents(
        prompt,
        OllamaTextPromptExecutionSettings(service_id=service_id, options=default_options),
    )

    responses = []
    async for line in response:
        if line:
            assert line[0].text == "test_response"
            responses.append(line[0].text)
    assert len(responses) == 1

    mock_chat_client.assert_called_once_with(
        model=model_id,
        messages=[{"role": "user", "content": prompt}],
        options=default_options,
        stream=True,
    )


@pytest.mark.asyncio
@patch("ollama.AsyncClient.chat")
async def test_streaming_text_completion_wrong_return_type(
    mock_chat_client,
    model_id,
    service_id,
    chat_history,
    default_options,
):
    """Test that the text completion streaming service fails when the return type is incorrect."""
    mock_chat_client.return_value = {"message": {"content": "test_response"}}  # should not be a non-streaming response

    ollama = OllamaChatCompletion(ai_model_id=model_id)
    with pytest.raises(ServiceInvalidResponseError):
        async for _ in ollama.get_streaming_text_contents(
            chat_history,
            OllamaTextPromptExecutionSettings(service_id=service_id, options=default_options),
        ):
            pass
