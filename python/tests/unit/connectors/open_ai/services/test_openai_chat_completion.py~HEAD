# Copyright (c) Microsoft. All rights reserved.


import pytest

from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import (
    OpenAIChatCompletion,
)
from semantic_kernel.const import USER_AGENT
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError


def test_init(openai_unit_test_env) -> None:
    # Test successful initialization
    open_ai_chat_completion = OpenAIChatCompletion()

    assert (
        open_ai_chat_completion.ai_model_id
        == openai_unit_test_env["OPENAI_CHAT_MODEL_ID"]
    )
    assert isinstance(open_ai_chat_completion, ChatCompletionClientBase)


def test_init_validation_fail() -> None:
    # Test successful initialization
    with pytest.raises(ServiceInitializationError):
        OpenAIChatCompletion(api_key="34523", ai_model_id={"test": "dict"})


def test_init_ai_model_id_constructor(openai_unit_test_env) -> None:
    # Test successful initialization
    ai_model_id = "test_model_id"
    open_ai_chat_completion = OpenAIChatCompletion(ai_model_id=ai_model_id)

    assert open_ai_chat_completion.ai_model_id == ai_model_id
    assert isinstance(open_ai_chat_completion, ChatCompletionClientBase)


def test_init_with_default_header(openai_unit_test_env) -> None:
    default_headers = {"X-Unit-Test": "test-guid"}

    # Test successful initialization
    open_ai_chat_completion = OpenAIChatCompletion(
        default_headers=default_headers,
    )

    assert (
        open_ai_chat_completion.ai_model_id
        == openai_unit_test_env["OPENAI_CHAT_MODEL_ID"]
    )
    assert isinstance(open_ai_chat_completion, ChatCompletionClientBase)

    # Assert that the default header we added is present in the client's default headers
    for key, value in default_headers.items():
        assert key in open_ai_chat_completion.client.default_headers
        assert open_ai_chat_completion.client.default_headers[key] == value


@pytest.mark.parametrize("exclude_list", [["OPENAI_CHAT_MODEL_ID"]], indirect=True)
def test_init_with_empty_model_id(openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        OpenAIChatCompletion(
            env_file_path="test.env",
        )


@pytest.mark.parametrize("exclude_list", [["OPENAI_API_KEY"]], indirect=True)
def test_init_with_empty_api_key(openai_unit_test_env) -> None:
    ai_model_id = "test_model_id"

    with pytest.raises(ServiceInitializationError):
        OpenAIChatCompletion(
            ai_model_id=ai_model_id,
            env_file_path="test.env",
        )


def test_serialize(openai_unit_test_env) -> None:
    default_headers = {"X-Unit-Test": "test-guid"}

    settings = {
        "ai_model_id": openai_unit_test_env["OPENAI_CHAT_MODEL_ID"],
        "api_key": openai_unit_test_env["OPENAI_API_KEY"],
        "default_headers": default_headers,
    }

    open_ai_chat_completion = OpenAIChatCompletion.from_dict(settings)
    dumped_settings = open_ai_chat_completion.to_dict()
    assert (
        dumped_settings["ai_model_id"] == openai_unit_test_env["OPENAI_CHAT_MODEL_ID"]
    )
    assert dumped_settings["api_key"] == openai_unit_test_env["OPENAI_API_KEY"]
    # Assert that the default header we added is present in the dumped_settings default headers
    for key, value in default_headers.items():
        assert key in dumped_settings["default_headers"]
        assert dumped_settings["default_headers"][key] == value
    # Assert that the 'User-agent' header is not present in the dumped_settings default headers
    assert USER_AGENT not in dumped_settings["default_headers"]


def test_serialize_with_org_id(openai_unit_test_env) -> None:
    settings = {
        "ai_model_id": openai_unit_test_env["OPENAI_CHAT_MODEL_ID"],
        "api_key": openai_unit_test_env["OPENAI_API_KEY"],
        "org_id": openai_unit_test_env["OPENAI_ORG_ID"],
    }

    open_ai_chat_completion = OpenAIChatCompletion.from_dict(settings)
    dumped_settings = open_ai_chat_completion.to_dict()
    assert (
        dumped_settings["ai_model_id"] == openai_unit_test_env["OPENAI_CHAT_MODEL_ID"]
    )
    assert dumped_settings["api_key"] == openai_unit_test_env["OPENAI_API_KEY"]
    assert dumped_settings["org_id"] == openai_unit_test_env["OPENAI_ORG_ID"]
    # Assert that the 'User-agent' header is not present in the dumped_settings default headers
    assert USER_AGENT not in dumped_settings["default_headers"]
