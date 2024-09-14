# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.ai.mistral_ai.prompt_execution_settings.mistral_ai_prompt_execution_settings import (
    MistralAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import (
    PromptExecutionSettings,
)


def test_default_mistralai_chat_prompt_execution_settings():
    settings = MistralAIChatPromptExecutionSettings()
    assert settings.temperature is None
    assert settings.top_p is None
    assert settings.max_tokens is None
    assert settings.messages is None


def test_custom_mistralai_chat_prompt_execution_settings():
    settings = MistralAIChatPromptExecutionSettings(
        temperature=0.5,
        top_p=0.5,
        max_tokens=128,
        messages=[{"role": "system", "content": "Hello"}],
    )
    assert settings.temperature == 0.5
    assert settings.top_p == 0.5
    assert settings.max_tokens == 128
    assert settings.messages == [{"role": "system", "content": "Hello"}]


def test_mistralai_chat_prompt_execution_settings_from_default_completion_config():
    settings = PromptExecutionSettings(service_id="test_service")
    chat_settings = MistralAIChatPromptExecutionSettings.from_prompt_execution_settings(
        settings
    )
    assert chat_settings.service_id == "test_service"
    assert chat_settings.temperature is None
    assert chat_settings.top_p is None
    assert chat_settings.max_tokens is None


def test_mistral_chat_prompt_execution_settings_from_openai_prompt_execution_settings():
    chat_settings = MistralAIChatPromptExecutionSettings(
        service_id="test_service", temperature=1.0
    )
    new_settings = MistralAIChatPromptExecutionSettings(
        service_id="test_2", temperature=0.0
    )
    chat_settings.update_from_prompt_execution_settings(new_settings)
    assert chat_settings.service_id == "test_2"
    assert chat_settings.temperature == 0.0


def test_mistral_chat_prompt_execution_settings_from_custom_completion_config():
    settings = PromptExecutionSettings(
        service_id="test_service",
        extension_data={
            "temperature": 0.5,
            "top_p": 0.5,
            "max_tokens": 128,
            "messages": [{"role": "system", "content": "Hello"}],
        },
    )
    chat_settings = MistralAIChatPromptExecutionSettings.from_prompt_execution_settings(
        settings
    )
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
    chat_settings = MistralAIChatPromptExecutionSettings.from_prompt_execution_settings(
        settings
    )
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
    chat_settings = MistralAIChatPromptExecutionSettings.from_prompt_execution_settings(
        settings
    )
    assert chat_settings.temperature == 0.5
    assert chat_settings.top_p == 0.5
    assert chat_settings.max_tokens == 128


def test_create_options():
    settings = MistralAIChatPromptExecutionSettings(
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


def test_create_options_with_function_choice_behavior():
    settings = MistralAIChatPromptExecutionSettings(
        service_id="test_service",
        function_choice_behavior="auto",
        extension_data={
            "temperature": 0.5,
            "top_p": 0.5,
            "max_tokens": 128,
            "tools": [{}],
            "messages": [{"role": "system", "content": "Hello"}],
        },
    )
    assert settings.function_choice_behavior
        
