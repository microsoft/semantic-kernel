# Copyright (c) Microsoft. All rights reserved.


import pytest

from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion import OpenAITextCompletion
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError


def test_open_ai_text_completion_init(openai_unit_test_env) -> None:
    # Test successful initialization
    open_ai_text_completion = OpenAITextCompletion()

    assert open_ai_text_completion.ai_model_id == openai_unit_test_env["OPENAI_TEXT_MODEL_ID"]
    assert isinstance(open_ai_text_completion, TextCompletionClientBase)


def test_open_ai_text_completion_init_with_ai_model_id(openai_unit_test_env) -> None:
    # Test successful initialization
    ai_model_id = "test_model_id"
    open_ai_text_completion = OpenAITextCompletion(ai_model_id=ai_model_id)

    assert open_ai_text_completion.ai_model_id == ai_model_id
    assert isinstance(open_ai_text_completion, TextCompletionClientBase)


def test_open_ai_text_completion_init_with_default_header(openai_unit_test_env) -> None:
    default_headers = {"X-Unit-Test": "test-guid"}

    # Test successful initialization
    open_ai_text_completion = OpenAITextCompletion(
        default_headers=default_headers,
    )

    assert open_ai_text_completion.ai_model_id == openai_unit_test_env["OPENAI_TEXT_MODEL_ID"]
    assert isinstance(open_ai_text_completion, TextCompletionClientBase)
    for key, value in default_headers.items():
        assert key in open_ai_text_completion.client.default_headers
        assert open_ai_text_completion.client.default_headers[key] == value


@pytest.mark.parametrize("exclude_list", [["OPENAI_API_KEY"]], indirect=True)
def test_open_ai_text_completion_init_with_empty_api_key(openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        OpenAITextCompletion()


def test_open_ai_text_completion_serialize(openai_unit_test_env) -> None:
    default_headers = {"X-Unit-Test": "test-guid"}

    settings = {
        "ai_model_id": openai_unit_test_env["OPENAI_TEXT_MODEL_ID"],
        "api_key": openai_unit_test_env["OPENAI_API_KEY"],
        "default_headers": default_headers,
    }

    open_ai_text_completion = OpenAITextCompletion.from_dict(settings)
    dumped_settings = open_ai_text_completion.to_dict()
    assert dumped_settings["ai_model_id"] == openai_unit_test_env["OPENAI_TEXT_MODEL_ID"]
    assert dumped_settings["api_key"] == openai_unit_test_env["OPENAI_API_KEY"]
    # Assert that the default header we added is present in the dumped_settings default headers
    for key, value in default_headers.items():
        assert key in dumped_settings["default_headers"]
        assert dumped_settings["default_headers"][key] == value


def test_open_ai_text_completion_serialize_with_org_id(openai_unit_test_env) -> None:
    settings = {
        "ai_model_id": openai_unit_test_env["OPENAI_TEXT_MODEL_ID"],
        "api_key": openai_unit_test_env["OPENAI_API_KEY"],
        "org_id": openai_unit_test_env["OPENAI_ORG_ID"],
    }

    open_ai_text_completion = OpenAITextCompletion.from_dict(settings)
    dumped_settings = open_ai_text_completion.to_dict()
    assert dumped_settings["ai_model_id"] == openai_unit_test_env["OPENAI_TEXT_MODEL_ID"]
    assert dumped_settings["api_key"] == openai_unit_test_env["OPENAI_API_KEY"]
    assert dumped_settings["org_id"] == openai_unit_test_env["OPENAI_ORG_ID"]
