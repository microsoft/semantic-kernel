# Copyright (c) Microsoft. All rights reserved.

from logging import Logger

import pytest
from pydantic import ValidationError

from semantic_kernel.connectors.ai import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai.const import (
    USER_AGENT,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import (
    OpenAIChatCompletion,
)
from semantic_kernel.connectors.ai.ai_exception import AIException


def test_open_ai_assistant_init() -> None:
    ai_model_id = "test_model_id"
    api_key = "test_api_key"
    logger = Logger("test_logger")

    # Test successful initialization
    assistant = OpenAIChatCompletion(
        ai_model_id=ai_model_id,
        api_key=api_key,
        log=logger,
        is_assistant=True,
    )

    assert assistant.ai_model_id == ai_model_id
    assert isinstance(assistant, ChatCompletionClientBase)
    assert assistant.is_assistant


def test_open_ai_assistant_with_default_header() -> None:
    ai_model_id = "test_model_id"
    api_key = "test_api_key"
    logger = Logger("test_logger")
    default_headers = {"X-Unit-Test": "test-guid"}

    # Test successful initialization
    assistant = OpenAIChatCompletion(
        ai_model_id=ai_model_id,
        api_key=api_key,
        log=logger,
        default_headers=default_headers,
        is_assistant=True,
    )

    assert assistant.ai_model_id == ai_model_id
    assert isinstance(assistant, ChatCompletionClientBase)
    assert assistant.is_assistant

    # Assert that the default header we added is present in the client's default headers
    for key, value in default_headers.items():
        assert key in assistant.client.default_headers
        assert assistant.client.default_headers[key] == value


def test_open_ai_assistant_with_empty_model_id() -> None:
    api_key = "test_api_key"
    logger = Logger("test_logger")

    with pytest.raises(ValidationError, match="ai_model_id"):
        OpenAIChatCompletion(
            ai_model_id="",
            api_key=api_key,
            log=logger,
            is_assistant=True,
        )


def test_open_ai_assistant_with_empty_api_key() -> None:
    ai_model_id = "test_model_id"
    logger = Logger("test_logger")

    with pytest.raises(ValidationError, match="api_key"):
        OpenAIChatCompletion(
            ai_model_id=ai_model_id,
            api_key="",
            log=logger,
            is_assistant=True
        )

@pytest.mark.asyncio
async def test_open_ai_assistant_with_chat_stream_raises_error() -> None:
    ai_model_id = "test_model_id"
    api_key = "test_api_key"
    logger = Logger("test_logger")
    default_headers = {"X-Unit-Test": "test-guid"}

    assistant = OpenAIChatCompletion(
        ai_model_id=ai_model_id,
        api_key=api_key,
        log=logger,
        default_headers=default_headers,
        is_assistant=True,
    )

    with pytest.raises(AIException):
        async for _ in assistant.complete_chat_stream_async(None, None):
            # Only start the generator to check for the exception
            break

def test_open_ai_assistant_serialize() -> None:
    ai_model_id = "test_model_id"
    api_key = "test_api_key"
    logger = Logger("test_logger")
    default_headers = {"X-Unit-Test": "test-guid"}

    settings = {
        "ai_model_id": ai_model_id,
        "api_key": api_key,
        "log": logger,
        "default_headers": default_headers,
        "is_assistant": True,
    }

    open_ai_chat_completion = OpenAIChatCompletion.from_dict(settings)
    dumped_settings = open_ai_chat_completion.to_dict()
    assert dumped_settings["ai_model_id"] == ai_model_id
    assert dumped_settings["api_key"] == api_key
    # Assert that the default header we added is present in the dumped_settings default headers
    for key, value in default_headers.items():
        assert key in dumped_settings["default_headers"]
        assert dumped_settings["default_headers"][key] == value
    # Assert that the 'User-agent' header is not present in the dumped_settings default headers
    assert USER_AGENT not in dumped_settings["default_headers"]
    assert dumped_settings["is_assistant"]


def test_open_ai_assistant_with_org_id() -> None:
    ai_model_id = "test_model_id"
    api_key = "test_api_key"
    org_id = "test_org_id"
    logger = Logger("test_logger")

    settings = {
        "ai_model_id": ai_model_id,
        "api_key": api_key,
        "org_id": org_id,
        "log": logger,
        "is_assistant": True,
    }

    open_ai_chat_completion = OpenAIChatCompletion.from_dict(settings)
    dumped_settings = open_ai_chat_completion.to_dict()
    assert dumped_settings["ai_model_id"] == ai_model_id
    assert dumped_settings["api_key"] == api_key
    assert dumped_settings["org_id"] == org_id
    # Assert that the 'User-agent' header is not present in the dumped_settings default headers
    assert USER_AGENT not in dumped_settings["default_headers"]
    assert dumped_settings["is_assistant"]
