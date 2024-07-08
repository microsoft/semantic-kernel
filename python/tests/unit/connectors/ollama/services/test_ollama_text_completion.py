# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import patch

import pytest

from semantic_kernel.connectors.ai.ollama.ollama_prompt_execution_settings import OllamaTextPromptExecutionSettings
from semantic_kernel.connectors.ai.ollama.services.ollama_text_completion import OllamaTextCompletion


def test_settings(model_id):
    ollama = OllamaTextCompletion(ai_model_id=model_id)
    settings = ollama.get_prompt_execution_settings_class()
    assert settings == OllamaTextPromptExecutionSettings


@pytest.mark.asyncio
@patch("ollama.AsyncClient.__init__", return_value=None)  # mock_client
@patch("ollama.AsyncClient.generate")  # mock_completion_client
async def test_custom_host(
    mock_completion_client, mock_client, model_id, service_id, host, chat_history, default_options
):
    mock_completion_client.return_value = {"response": "test_response"}

    ollama = OllamaTextCompletion(ai_model_id=model_id, host=host)
    _ = await ollama.get_text_contents(
        chat_history,
        OllamaTextPromptExecutionSettings(service_id=service_id, options=default_options),
    )

    mock_client.assert_called_once_with(host=host)


@pytest.mark.asyncio
@patch("ollama.AsyncClient.__init__", return_value=None)  # mock_client
@patch("ollama.AsyncClient.generate")  # mock_completion_client
async def test_custom_host_streaming(
    mock_completion_client, mock_client, model_id, service_id, host, chat_history, default_options
):
    mock_completion_client.__aiter__.return_value = {"response": "test_response"}

    ollama = OllamaTextCompletion(ai_model_id=model_id, host=host)
    async for _ in ollama.get_streaming_text_contents(
        chat_history,
        OllamaTextPromptExecutionSettings(service_id=service_id, options=default_options),
    ):
        pass

    mock_client.assert_called_once_with(host=host)


@pytest.mark.asyncio
@patch("ollama.AsyncClient.generate")
async def test_complete(mock_completion_client, model_id, service_id, prompt, default_options):
    mock_completion_client.return_value = {"response": "test_response"}

    ollama = OllamaTextCompletion(ai_model_id=model_id)
    response = await ollama.get_text_contents(
        prompt,
        OllamaTextPromptExecutionSettings(service_id=service_id, options=default_options),
    )

    assert response[0].text == "test_response"
    mock_completion_client.assert_called_once_with(
        model=model_id,
        prompt=prompt,
        options=default_options,
        stream=False,
    )


@pytest.mark.asyncio
@patch("ollama.AsyncClient.generate")
async def test_complete_stream(mock_completion_client, model_id, service_id, prompt, default_options):
    mock_completion_client.__aiter__.return_value = {"response": "test_response"}

    ollama = OllamaTextCompletion(ai_model_id=model_id)
    response = ollama.get_streaming_text_contents(
        prompt,
        OllamaTextPromptExecutionSettings(service_id=service_id, options=default_options),
    )

    async for line in response:
        if line:
            assert line[0].text == "test_response"
    mock_completion_client.assert_called_once_with(
        model=model_id,
        prompt=prompt,
        options=default_options,
        stream=True,
    )
