# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.connectors.ai.anthropic.prompt_execution_settings.anthropic_prompt_execution_settings import (
    AnthropicChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.exceptions import ServiceInvalidExecutionSettingsError


def test_default_anthropic_chat_prompt_execution_settings():
    settings = AnthropicChatPromptExecutionSettings()
    assert settings.temperature is None
    assert settings.top_p is None
    assert settings.max_tokens == 1024
    assert settings.messages is None


def test_custom_anthropic_chat_prompt_execution_settings():
    settings = AnthropicChatPromptExecutionSettings(
        temperature=0.5,
        top_p=0.5,
        max_tokens=128,
        messages=[{"role": "system", "content": "Hello"}],
    )
    assert settings.temperature == 0.5
    assert settings.top_p == 0.5
    assert settings.max_tokens == 128
    assert settings.messages == [{"role": "system", "content": "Hello"}]


def test_anthropic_chat_prompt_execution_settings_from_default_completion_config():
    settings = PromptExecutionSettings(service_id="test_service")
    chat_settings = AnthropicChatPromptExecutionSettings.from_prompt_execution_settings(settings)
    assert chat_settings.service_id == "test_service"
    assert chat_settings.temperature is None
    assert chat_settings.top_p is None
    assert chat_settings.max_tokens == 1024


def test_anthropic_chat_prompt_execution_settings_from_openai_prompt_execution_settings():
    chat_settings = AnthropicChatPromptExecutionSettings(service_id="test_service", temperature=1.0)
    new_settings = AnthropicChatPromptExecutionSettings(service_id="test_2", temperature=0.0)
    chat_settings.update_from_prompt_execution_settings(new_settings)
    assert chat_settings.service_id == "test_2"
    assert chat_settings.temperature == 0.0


def test_anthropic_chat_prompt_execution_settings_from_custom_completion_config():
    settings = PromptExecutionSettings(
        service_id="test_service",
        extension_data={
            "temperature": 0.5,
            "top_p": 0.5,
            "max_tokens": 128,
            "messages": [{"role": "system", "content": "Hello"}],
        },
    )
    chat_settings = AnthropicChatPromptExecutionSettings.from_prompt_execution_settings(settings)
    assert chat_settings.temperature == 0.5
    assert chat_settings.top_p == 0.5
    assert chat_settings.max_tokens == 128


def test_openai_chat_prompt_execution_settings_from_custom_completion_config_with_none():
    settings = PromptExecutionSettings(
        service_id="test_service",
        extension_data={
            "temperature": 0.5,
            "top_p": 0.5,
            "max_tokens": 128,
            "messages": [{"role": "system", "content": "Hello"}],
        },
    )
    chat_settings = AnthropicChatPromptExecutionSettings.from_prompt_execution_settings(settings)
    assert chat_settings.temperature == 0.5
    assert chat_settings.top_p == 0.5
    assert chat_settings.max_tokens == 128


def test_openai_chat_prompt_execution_settings_from_custom_completion_config_with_functions():
    settings = PromptExecutionSettings(
        service_id="test_service",
        extension_data={
            "temperature": 0.5,
            "top_p": 0.5,
            "max_tokens": 128,
            "tools": [{}],
            "messages": [{"role": "system", "content": "Hello"}],
        },
    )
    chat_settings = AnthropicChatPromptExecutionSettings.from_prompt_execution_settings(settings)
    assert chat_settings.temperature == 0.5
    assert chat_settings.top_p == 0.5
    assert chat_settings.max_tokens == 128


def test_create_options():
    settings = AnthropicChatPromptExecutionSettings(
        service_id="test_service",
        extension_data={
            "temperature": 0.5,
            "top_p": 0.5,
            "max_tokens": 128,
            "tools": [{}],
            "messages": [{"role": "system", "content": "Hello"}],
        },
    )
    options = settings.prepare_settings_dict()
    assert options["temperature"] == 0.5
    assert options["top_p"] == 0.5
    assert options["max_tokens"] == 128


def test_tool_choice_none():
    with pytest.raises(ServiceInvalidExecutionSettingsError, match="Tool choice 'none' is not supported by Anthropic."):
        AnthropicChatPromptExecutionSettings(
            service_id="test_service",
            extension_data={
                "temperature": 0.5,
                "top_p": 0.5,
                "max_tokens": 128,
                "tool_choice": {"type": "none"},
                "messages": [{"role": "system", "content": "Hello"}],
            },
            function_choice_behavior=FunctionChoiceBehavior.NoneInvoke(),
        )
