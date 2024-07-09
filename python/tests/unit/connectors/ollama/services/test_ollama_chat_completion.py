# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import patch

import pytest

from semantic_kernel.connectors.ai.ollama.ollama_prompt_execution_settings import OllamaChatPromptExecutionSettings
from semantic_kernel.connectors.ai.ollama.services.ollama_chat_completion import OllamaChatCompletion
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError


def test_settings(model_id):
    ollama = OllamaChatCompletion(ai_model_id=model_id)
    settings = ollama.get_prompt_execution_settings_class()
    assert settings == OllamaChatPromptExecutionSettings


def test_init_empty_service_id(model_id):
    ollama = OllamaChatCompletion(ai_model_id=model_id)
    assert ollama.service_id == model_id


@pytest.mark.parametrize("exclude_list", [["OLLAMA_MODEL"]], indirect=True)
def test_init_empty_model_id(ollama_unit_test_env):
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
    mock_chat_client.return_value = {"message": {"content": "test_response"}}

    ollama = OllamaChatCompletion(ai_model_id=model_id, host=host)
    _ = await ollama.get_chat_message_contents(
        chat_history,
        OllamaChatPromptExecutionSettings(service_id=service_id, options=default_options),
    )
    _ = await ollama.get_text_contents(
        prompt,
        OllamaChatPromptExecutionSettings(service_id=service_id, options=default_options),
    )

    assert mock_client.call_count == 2
    mock_client.assert_called_with(host=host)


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
    mock_chat_client.return_value = mock_streaming_chat_response

    ollama = OllamaChatCompletion(ai_model_id=model_id, host=host)
    async for _ in ollama.get_streaming_chat_message_contents(
        chat_history,
        OllamaChatPromptExecutionSettings(service_id=service_id, options=default_options),
    ):
        pass
    async for _ in ollama.get_streaming_text_contents(
        prompt,
        OllamaChatPromptExecutionSettings(service_id=service_id, options=default_options),
    ):
        pass

    assert mock_client.call_count == 2
    mock_client.assert_called_with(host=host)


@pytest.mark.asyncio
@patch("ollama.AsyncClient.chat")
async def test_complete_chat(mock_chat_client, model_id, service_id, chat_history, default_options):
    mock_chat_client.return_value = {"message": {"content": "test_response"}}

    ollama = OllamaChatCompletion(ai_model_id=model_id)
    response = await ollama.get_chat_message_contents(
        chat_history,
        OllamaChatPromptExecutionSettings(service_id=service_id, options=default_options),
    )

    assert response[0].content == "test_response"
    mock_chat_client.assert_called_once_with(
        model=model_id,
        messages=ollama._prepare_chat_history_for_request(chat_history),
        options=default_options,
        stream=False,
    )


@pytest.mark.asyncio
@patch("ollama.AsyncClient.chat")
async def test_complete(mock_chat_client, model_id, service_id, prompt, default_options):
    mock_chat_client.return_value = {"message": {"content": "test_response"}}
    ollama = OllamaChatCompletion(ai_model_id=model_id)
    response = await ollama.get_text_contents(
        prompt,
        OllamaChatPromptExecutionSettings(service_id=service_id, options=default_options),
    )

    assert response[0].text == "test_response"
    mock_chat_client.assert_called_once_with(
        model=model_id,
        messages=[{"role": "user", "content": prompt}],
        options=default_options,
        stream=False,
    )


@pytest.mark.asyncio
@patch("ollama.AsyncClient.chat")
async def test_complete_chat_stream(
    mock_chat_client,
    mock_streaming_chat_response,
    model_id,
    service_id,
    chat_history,
    default_options,
):
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
async def test_complete_stream(
    mock_chat_client,
    mock_streaming_chat_response,
    model_id,
    service_id,
    prompt,
    default_options,
):
    mock_chat_client.return_value = mock_streaming_chat_response

    ollama = OllamaChatCompletion(ai_model_id=model_id)
    response = ollama.get_streaming_text_contents(
        prompt,
        OllamaChatPromptExecutionSettings(service_id=service_id, options=default_options),
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
