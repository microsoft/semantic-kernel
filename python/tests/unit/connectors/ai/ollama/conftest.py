# Copyright (c) Microsoft. All rights reserved.

from collections.abc import AsyncGenerator, AsyncIterator
from unittest.mock import MagicMock

import pytest
from ollama import AsyncClient

from semantic_kernel.contents.chat_history import ChatHistory


@pytest.fixture()
def model_id() -> str:
    return "test_model_id"


@pytest.fixture()
def service_id() -> str:
    return "test_service_id"


@pytest.fixture()
def host() -> str:
    return "http://localhost:5000"


@pytest.fixture()
def custom_client() -> AsyncClient:
    return AsyncClient("http://localhost:5001")


@pytest.fixture()
def chat_history() -> ChatHistory:
    chat_history = ChatHistory()
    chat_history.add_user_message("test_prompt")
    return chat_history


@pytest.fixture()
def prompt() -> str:
    return "test_prompt"


@pytest.fixture()
def default_options() -> dict:
    return {"test": "test"}


@pytest.fixture()
def ollama_unit_test_env(monkeypatch, model_id, host, exclude_list):
    """Fixture to set environment variables for OllamaSettings."""
    if exclude_list is None:
        exclude_list = []

    env_vars = {
        "OLLAMA_MODEL": model_id,
        "OLLAMA_HOST": host,
    }

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@pytest.fixture()
def mock_streaming_text_response() -> AsyncIterator:
    streaming_text_response = MagicMock(spec=AsyncGenerator)
    streaming_text_response.__aiter__.return_value = [{"response": "test_response"}]

    return streaming_text_response


@pytest.fixture()
def mock_streaming_chat_response() -> AsyncIterator:
    streaming_chat_response = MagicMock(spec=AsyncGenerator)
    streaming_chat_response.__aiter__.return_value = [
        {"message": {"content": "test_response"}}
    ]

    return streaming_chat_response
