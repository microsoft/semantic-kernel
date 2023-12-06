# Copyright (c) Microsoft. All rights reserved.

from logging import Logger

import pytest
from pydantic import ValidationError

from semantic_kernel.connectors.ai import TextCompletionClientBase
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion import (
    OpenAITextCompletion,
)


def test_open_ai_text_completion_init() -> None:
    ai_model_id = "test_model_id"
    api_key = "test_api_key"
    logger = Logger("test_logger")

    # Test successful initialization
    open_ai_text_completion = OpenAITextCompletion(
        ai_model_id=ai_model_id,
        api_key=api_key,
        log=logger,
    )

    assert open_ai_text_completion.ai_model_id == ai_model_id
    assert isinstance(open_ai_text_completion, TextCompletionClientBase)


def test_open_ai_text_completion_init_with_default_header() -> None:
    ai_model_id = "test_model_id"
    api_key = "test_api_key"
    logger = Logger("test_logger")
    default_headers = {"X-Unit-Test": "test-guid"}

    # Test successful initialization
    open_ai_text_completion = OpenAITextCompletion(
        ai_model_id=ai_model_id,
        api_key=api_key,
        log=logger,
        default_headers=default_headers,
    )

    assert open_ai_text_completion.ai_model_id == ai_model_id
    assert isinstance(open_ai_text_completion, TextCompletionClientBase)
    for key, value in default_headers.items():
        assert key in open_ai_text_completion.client.default_headers
        assert open_ai_text_completion.client.default_headers[key] == value


def test_open_ai_text_completion_init_with_empty_model_id() -> None:
    # ai_model_id = "test_model_id"
    api_key = "test_api_key"
    logger = Logger("test_logger")

    with pytest.raises(ValidationError, match="ai_model_id"):
        OpenAITextCompletion(
            ai_model_id="",
            api_key=api_key,
            log=logger,
        )


def test_open_ai_text_completion_init_with_empty_api_key() -> None:
    ai_model_id = "test_model_id"
    # api_key = "test_api_key"
    logger = Logger("test_logger")

    with pytest.raises(ValidationError, match="api_key"):
        OpenAITextCompletion(
            ai_model_id=ai_model_id,
            api_key="",
            log=logger,
        )


def test_open_ai_text_completion_serialize() -> None:
    ai_model_id = "test_model_id"
    api_key = "test_api_key"
    logger = Logger("test_logger")
    default_headers = {"X-Unit-Test": "test-guid"}

    settings = {
        "ai_model_id": ai_model_id,
        "api_key": api_key,
        "log": logger,
        "default_headers": default_headers,
    }

    open_ai_text_completion = OpenAITextCompletion.from_dict(settings)
    dumped_settings = open_ai_text_completion.to_dict()
    assert dumped_settings["ai_model_id"] == ai_model_id
    assert dumped_settings["api_key"] == api_key
    # Assert that the default header we added is present in the dumped_settings default headers
    for key, value in default_headers.items():
        assert key in dumped_settings["default_headers"]
        assert dumped_settings["default_headers"][key] == value


def test_open_ai_text_completion_serialize_with_org_id() -> None:
    ai_model_id = "test_model_id"
    api_key = "test_api_key"
    org_id = "test_org_id"
    logger = Logger("test_logger")

    settings = {
        "ai_model_id": ai_model_id,
        "api_key": api_key,
        "org_id": org_id,
        "log": logger,
    }

    open_ai_text_completion = OpenAITextCompletion.from_dict(settings)
    dumped_settings = open_ai_text_completion.to_dict()
    assert dumped_settings["ai_model_id"] == ai_model_id
    assert dumped_settings["api_key"] == api_key
    assert dumped_settings["org_id"] == org_id
