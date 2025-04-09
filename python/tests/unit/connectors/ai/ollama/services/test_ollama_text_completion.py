# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import patch

import pytest

from semantic_kernel.connectors.ai.ollama.ollama_prompt_execution_settings import OllamaTextPromptExecutionSettings
from semantic_kernel.connectors.ai.ollama.services.ollama_text_completion import OllamaTextCompletion
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError, ServiceInvalidResponseError


def test_settings(model_id):
    """Test that the settings class is correct"""
    ollama = OllamaTextCompletion(ai_model_id=model_id)
    settings = ollama.get_prompt_execution_settings_class()
    assert settings == OllamaTextPromptExecutionSettings


def test_init_empty_service_id(model_id):
    """Test that the service initializes correctly with an empty service_id"""
    ollama = OllamaTextCompletion(ai_model_id=model_id)
    assert ollama.service_id == model_id


def test_custom_client(model_id, custom_client):
    """Test that the service initializes correctly with a custom client."""
    ollama = OllamaTextCompletion(ai_model_id=model_id, client=custom_client)
    assert ollama.client == custom_client


def test_invalid_ollama_settings():
    """Test that the service initializes incorrectly with invalid settings."""
    with pytest.raises(ServiceInitializationError):
        _ = OllamaTextCompletion(ai_model_id=123)


def test_service_url(ollama_unit_test_env):
    """Test that the service URL is correct."""
    ollama = OllamaTextCompletion()
    assert ollama.service_url() == ollama_unit_test_env["OLLAMA_HOST"]


@pytest.mark.parametrize("exclude_list", [["OLLAMA_TEXT_MODEL_ID"]], indirect=True)
def test_init_empty_model_id(ollama_unit_test_env):
    """Test that the service initializes incorrectly with an empty model_id"""
    with pytest.raises(ServiceInitializationError):
        _ = OllamaTextCompletion(env_file_path="fake_env_file_path.env")


@patch("ollama.AsyncClient.__init__", return_value=None)  # mock_client
@patch("ollama.AsyncClient.generate")  # mock_completion_client
async def test_custom_host(
    mock_completion_client, mock_client, model_id, service_id, host, chat_history, default_options
):
    """Test that the service initializes and generates content correctly with a custom host."""
    mock_completion_client.return_value = {"response": "test_response"}

    ollama = OllamaTextCompletion(ai_model_id=model_id, host=host)
    _ = await ollama.get_text_contents(
        chat_history,
        OllamaTextPromptExecutionSettings(service_id=service_id, options=default_options),
    )

    mock_client.assert_called_once_with(host=host)


@patch("ollama.AsyncClient.__init__", return_value=None)  # mock_client
@patch("ollama.AsyncClient.generate")  # mock_completion_client
async def test_custom_host_streaming(
    mock_completion_client, mock_client, model_id, service_id, host, chat_history, default_options
):
    """Test that the service initializes and generates streaming content correctly with a custom host."""
    mock_completion_client.__aiter__.return_value = {"response": "test_response"}

    ollama = OllamaTextCompletion(ai_model_id=model_id, host=host)
    async for _ in ollama.get_streaming_text_contents(
        chat_history,
        OllamaTextPromptExecutionSettings(service_id=service_id, options=default_options),
    ):
        pass

    mock_client.assert_called_once_with(host=host)


@patch("ollama.AsyncClient.generate")
async def test_completion(mock_completion_client, model_id, service_id, prompt, default_options):
    """Test that the service generates content correctly."""
    mock_completion_client.return_value = {"response": "test_response"}

    ollama = OllamaTextCompletion(ai_model_id=model_id)
    response = await ollama.get_text_contents(
        prompt=prompt,
        settings=OllamaTextPromptExecutionSettings(service_id=service_id, options=default_options),
    )

    assert response[0].text == "test_response"
    mock_completion_client.assert_called_once_with(
        model=model_id,
        prompt=prompt,
        options=default_options,
        stream=False,
    )


@patch("ollama.AsyncClient.generate")
async def test_completion_wrong_return_type(
    mock_completion_client,
    mock_streaming_text_response,
    model_id,
    service_id,
    chat_history,
    default_options,
):
    """Test that the completion service fails when the return type is incorrect."""
    mock_completion_client.return_value = mock_streaming_text_response  # should not be a streaming response

    ollama = OllamaTextCompletion(ai_model_id=model_id)
    with pytest.raises(ServiceInvalidResponseError):
        await ollama.get_text_contents(
            chat_history,
            OllamaTextPromptExecutionSettings(service_id=service_id, options=default_options),
        )


@patch("ollama.AsyncClient.generate")
async def test_streaming_completion(
    mock_completion_client,
    mock_streaming_text_response,
    model_id,
    service_id,
    prompt,
    default_options,
):
    """Test that the service generates streaming content correctly."""
    mock_completion_client.return_value = mock_streaming_text_response

    ollama = OllamaTextCompletion(ai_model_id=model_id)
    response = ollama.get_streaming_text_contents(
        prompt,
        OllamaTextPromptExecutionSettings(service_id=service_id, options=default_options),
    )

    responses = []
    async for line in response:
        assert line[0].text == "test_response"
        responses.append(line)
    assert len(responses) == 1

    mock_completion_client.assert_called_once_with(
        model=model_id,
        prompt=prompt,
        options=default_options,
        stream=True,
    )


@patch("ollama.AsyncClient.generate")
async def test_streaming_completion_wrong_return_type(
    mock_completion_client,
    model_id,
    service_id,
    chat_history,
    default_options,
):
    """Test that the streaming completion service fails when the return type is incorrect."""
    mock_completion_client.return_value = {"response": "test_response"}  # should not be a non-streaming response

    ollama = OllamaTextCompletion(ai_model_id=model_id)
    with pytest.raises(ServiceInvalidResponseError):
        async for _ in ollama.get_streaming_text_contents(
            chat_history,
            OllamaTextPromptExecutionSettings(service_id=service_id, options=default_options),
        ):
            pass
