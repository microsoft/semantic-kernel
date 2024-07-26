# Copyright (c) Microsoft. All rights reserved.

import pytest
from pydantic import ValidationError

from semantic_kernel.agents.open_ai.open_ai_assistant_invocation_options import OpenAIAssistantInvocationOptions


def test_default_values():
    options = OpenAIAssistantInvocationOptions()
    assert options.ai_model_id is None
    assert options.enable_code_interpreter is False
    assert options.enable_file_search is False
    assert options.enable_json_response is False
    assert options.max_completion_tokens is None
    assert options.max_prompt_tokens is None
    assert options.parallel_tool_calls_enabled is True
    assert options.truncation_message_count is None
    assert options.temperature is None
    assert options.top_p is None
    assert options.metadata == {}


def test_setting_values():
    options = OpenAIAssistantInvocationOptions(
        ai_model_id="test_model",
        enable_code_interpreter=True,
        enable_file_search=True,
        enable_json_response=True,
        max_completion_tokens=100,
        max_prompt_tokens=50,
        parallel_tool_calls_enabled=True,
        truncation_message_count=10,
        temperature=0.7,
        top_p=0.9,
        metadata={"key1": "value1", "key2": "value2"},
    )
    assert options.ai_model_id == "test_model"
    assert options.enable_code_interpreter is True
    assert options.enable_file_search is True
    assert options.enable_json_response is True
    assert options.max_completion_tokens == 100
    assert options.max_prompt_tokens == 50
    assert options.parallel_tool_calls_enabled is True
    assert options.truncation_message_count == 10
    assert options.temperature == 0.7
    assert options.top_p == 0.9
    assert options.metadata == {"key1": "value1", "key2": "value2"}


def test_metadata_max_length():
    valid_metadata = {f"key{i}": f"value{i}" for i in range(16)}
    options = OpenAIAssistantInvocationOptions(metadata=valid_metadata)
    assert options.metadata == valid_metadata

    invalid_metadata = {f"key{i}": f"value{i}" for i in range(17)}
    with pytest.raises(ValidationError):
        OpenAIAssistantInvocationOptions(metadata=invalid_metadata)


def test_invalid_temperature_value():
    with pytest.raises(ValidationError):
        OpenAIAssistantInvocationOptions(temperature=-3.1)

    with pytest.raises(ValidationError):
        OpenAIAssistantInvocationOptions(temperature=3.1)


def test_invalid_top_p_value():
    with pytest.raises(ValidationError):
        OpenAIAssistantInvocationOptions(top_p=-1.1)

    with pytest.raises(ValidationError):
        OpenAIAssistantInvocationOptions(top_p=1.1)


def test_valid_temperature_value():
    options = OpenAIAssistantInvocationOptions(temperature=0.5)
    assert options.temperature == 0.5


def test_valid_top_p_value():
    options = OpenAIAssistantInvocationOptions(top_p=0.5)
    assert options.top_p == 0.5
