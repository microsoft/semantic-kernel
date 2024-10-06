<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
# Copyright (c) Microsoft. All rights reserved.

=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
# Copyright (c) Microsoft. All rights reserved.

=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
# Copyright (c) Microsoft. All rights reserved.

=======
>>>>>>> Stashed changes
<<<<<<< HEAD
# Copyright (c) Microsoft. All rights reserved.

=======
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
from unittest.mock import patch

import pytest

from semantic_kernel.connectors.ai.ollama.ollama_prompt_execution_settings import (
    OllamaChatPromptExecutionSettings,
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    OllamaTextPromptExecutionSettings,
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    OllamaTextPromptExecutionSettings,
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
    OllamaTextPromptExecutionSettings,
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    OllamaTextPromptExecutionSettings,
=======
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
)
from semantic_kernel.connectors.ai.ollama.services.ollama_chat_completion import (
    OllamaChatCompletion,
)
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
from semantic_kernel.exceptions.service_exceptions import (
    ServiceInitializationError,
    ServiceInvalidResponseError,
)
>>>>>>>+main
_kernel.connectors.ai.ollama.ollama_prompt_execution_settings import OllamaChatPromptExecutionSettings
from semantic_kernel.connectors.ai.ollama.services.ollama_chat_completion import OllamaChatCompletion
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError, ServiceInvalidResponseError


def test_settings(model_id):
    """Test that the settings class is correct."""
    ollama = OllamaChatCompletion(ai_model_id=model_id)
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
from semantic_kernel.contents.chat_history import ChatHistory
from tests.unit.connectors.ollama.utils import MockResponse


def test_settings():
    ollama = OllamaChatCompletion(ai_model_id="test_model")
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
    settings = ollama.get_prompt_execution_settings_class()
    assert settings == OllamaChatPromptExecutionSettings


<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
def test_init_empty_service_id(model_id):
    """Test that the service initializes correctly with an empty service id."""
    ollama = OllamaChatCompletion(ai_model_id=model_id)
    assert ollama.service_id == model_id


<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
def test_init_empty_ai_model_id():
    """Test that the service initializes with a error if there is no ai_model_id."""
    with pytest.raises(ServiceInitializationError):
        _ = OllamaChatCompletion()


<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
def test_init_empty_string_ai_model_id():
    """Test that the service initializes with a error if there is no ai_model_id."""
    with pytest.raises(ServiceInitializationError):
        _ = OllamaChatCompletion(ai_model_id="")


def test_custom_client(model_id, custom_client):
    """Test that the service initializes correctly with a custom client."""
    ollama = OllamaChatCompletion(ai_model_id=model_id, client=custom_client)
    assert ollama.client == custom_client


@pytest.mark.parametrize("exclude_list", [["OLLAMA_MODEL"]], indirect=True)
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
def test_init_empty_model_id(ollama_unit_test_env):
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
def test_init_empty_model_id(ollama_unit_test_env):
=======
def test_init_empty_model_id_in_env(ollama_unit_test_env):
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
def test_init_empty_model_id_in_env(ollama_unit_test_env):
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
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
        OllamaChatPromptExecutionSettings(
            service_id=service_id, options=default_options
        ),
    )

    text_responses = await ollama.get_text_contents(
        prompt,
        OllamaTextPromptExecutionSettings(
            service_id=service_id, options=default_options
        ),
    )

    # Check that the client was initialized once with the correct host
    assert mock_client.call_count == 1
    mock_client.assert_called_with(host=host)
    # Check that the chat client was called once and the responses are correct
    assert mock_chat_client.call_count == 1
    assert len(chat_responses) == 1
    assert chat_responses[0].content == "test_response"


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
        OllamaChatPromptExecutionSettings(
            service_id=service_id, options=default_options
        ),
    ):
        assert len(messages) == 1
        assert messages[0].role == "assistant"
        assert messages[0].content == "test_response"

    async for messages in ollama.get_streaming_text_contents(
        prompt,
        OllamaTextPromptExecutionSettings(
            service_id=service_id, options=default_options
        ),
    ):
        assert len(messages) == 1
        assert messages[0].text == "test_response"

    # Check that the client was initialized once with the correct host
    assert mock_client.call_count == 1
    mock_client.assert_called_with(host=host)
    # Check that the chat client was called once
    assert mock_chat_client.call_count == 1


@pytest.mark.asyncio
@patch("ollama.AsyncClient.chat")
async def test_chat_completion(
    mock_chat_client, model_id, service_id, chat_history, default_options
):
    """Test that the chat completion service completes correctly."""
    mock_chat_client.return_value = {"message": {"content": "test_response"}}

    ollama = OllamaChatCompletion(ai_model_id=model_id)
    response = await ollama.get_chat_message_contents(
        chat_history=chat_history,
        settings=OllamaChatPromptExecutionSettings(
            service_id=service_id, options=default_options
        ),
    )

    assert len(response) == 1
    assert response[0].content == "test_response"
    mock_chat_client.assert_called_once_with(
        model=model_id,
        messages=ollama._prepare_chat_history_for_request(chat_history),
        options=default_options,
        stream=False,
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
@pytest.mark.asyncio
@patch("aiohttp.ClientSession.post")
async def test_complete_chat(mock_post):
    mock_post.return_value = MockResponse(response={"message": {"content": "test_response"}})
    ollama = OllamaChatCompletion(ai_model_id="test_model")
    chat_history = ChatHistory()
    chat_history.add_user_message("test_prompt")
    response = await ollama.complete_chat(
        chat_history,
        OllamaChatPromptExecutionSettings(service_id="test_model", ai_model_id="test_model", options={"test": "test"}),
    )
    assert response[0].content == "test_response"
    mock_post.assert_called_once_with(
        "http://localhost:11434/api/chat",
        json={
            "model": "test_model",
            "messages": [{"role": "user", "content": "test_prompt"}],
            "options": {"test": "test"},
            "stream": False,
        },
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
    )


@pytest.mark.asyncio
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
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
    mock_chat_client.return_value = (
        mock_streaming_chat_response  # should not be a streaming response
    )

    ollama = OllamaChatCompletion(ai_model_id=model_id)
    with pytest.raises(ServiceInvalidResponseError):
        await ollama.get_chat_message_contents(
            chat_history,
            OllamaChatPromptExecutionSettings(
                service_id=service_id, options=default_options
            ),
        )


@pytest.mark.asyncio
@patch("ollama.AsyncClient.chat")
async def test_text_completion(
    mock_chat_client, model_id, service_id, prompt, default_options
):
    """Test that the text completion service completes correctly."""
    mock_chat_client.return_value = {"message": {"content": "test_response"}}
    ollama = OllamaChatCompletion(ai_model_id=model_id)
    response = await ollama.get_text_contents(
        prompt=prompt,
        settings=OllamaTextPromptExecutionSettings(
            service_id=service_id, options=default_options
        ),
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
    mock_chat_client.return_value = (
        mock_streaming_chat_response  # should not be a streaming response
    )

    ollama = OllamaChatCompletion(ai_model_id=model_id)
    with pytest.raises(ServiceInvalidResponseError):
        await ollama.get_text_contents(
            chat_history,
            OllamaTextPromptExecutionSettings(
                service_id=service_id, options=default_options
            ),
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
        OllamaChatPromptExecutionSettings(
            service_id=service_id, options=default_options
        ),
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
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
    )


@pytest.mark.asyncio
=======
=======
<<<<<<< Updated upstream
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
@patch("aiohttp.ClientSession.post")
async def test_complete(mock_post):
    mock_post.return_value = MockResponse(response={"message": {"content": "test_response"}})
    ollama = OllamaChatCompletion(ai_model_id="test_model")
    response = await ollama.complete(
        "test_prompt",
        OllamaChatPromptExecutionSettings(service_id="test_model", ai_model_id="test_model", options={"test": "test"}),
    )
    assert response[0].text == "test_response"


@pytest.mark.asyncio
@patch("aiohttp.ClientSession.post")
async def test_complete_chat_stream(mock_post):
    mock_post.return_value = MockResponse(response={"message": {"content": "test_response"}})
    ollama = OllamaChatCompletion(ai_model_id="test_model")
    chat_history = ChatHistory()
    chat_history.add_user_message("test_prompt")
    response = ollama.complete_chat_stream(
        chat_history,
        OllamaChatPromptExecutionSettings(ai_model_id="test_model", options={"test": "test"}),
    )
    async for line in response:
        if line:
            assert line[0].content == "test_response"
    mock_post.assert_called_once_with(
        "http://localhost:11434/api/chat",
        json={
            "model": "test_model",
            "messages": [{"role": "user", "content": "test_prompt"}],
            "options": {"test": "test"},
            "stream": True,
        },
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
    )


@pytest.mark.asyncio
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
@patch("ollama.AsyncClient.chat")
async def test_streaming_chat_completion_wrong_return_type(
    mock_chat_client,
    model_id,
    service_id,
    chat_history,
    default_options,
):
    """Test that the chat completion streaming service fails when the return type is incorrect."""
    mock_chat_client.return_value = {
        "message": {"content": "test_response"}
    }  # should not be a non-streaming response

    ollama = OllamaChatCompletion(ai_model_id=model_id)
    with pytest.raises(ServiceInvalidResponseError):
        async for _ in ollama.get_streaming_chat_message_contents(
            chat_history,
            OllamaChatPromptExecutionSettings(
                service_id=service_id, options=default_options
            ),
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
        OllamaTextPromptExecutionSettings(
            service_id=service_id, options=default_options
        ),
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
    mock_chat_client.return_value = {
        "message": {"content": "test_response"}
    }  # should not be a non-streaming response

    ollama = OllamaChatCompletion(ai_model_id=model_id)
    with pytest.raises(ServiceInvalidResponseError):
        async for _ in ollama.get_streaming_text_contents(
            chat_history,
            OllamaTextPromptExecutionSettings(
                service_id=service_id, options=default_options
            ),
        ):
            pass
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
@patch("aiohttp.ClientSession.post")
async def test_complete_stream(mock_post):
    mock_post.return_value = MockResponse(response={"message": {"content": "test_response"}})
    ollama = OllamaChatCompletion(ai_model_id="test_model")
    response = ollama.complete_stream(
        "test_prompt",
        OllamaChatPromptExecutionSettings(ai_model_id="test_model", options={"test": "test"}),
    )
    async for line in response:
        if line:
            assert line[0].text == "test_response"
    mock_post.assert_called_once_with(
        "http://localhost:11434/api/chat",
        json={
            "model": "test_model",
            "options": {"test": "test"},
            "stream": True,
            "messages": [{"role": "user", "content": "test_prompt"}],
        },
    )
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
