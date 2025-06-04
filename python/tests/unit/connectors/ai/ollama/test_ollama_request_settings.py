# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.ai.ollama import OllamaPromptExecutionSettings
from semantic_kernel.connectors.ai.ollama.ollama_prompt_execution_settings import (
    OllamaChatPromptExecutionSettings,
    OllamaTextPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


def test_default_ollama_prompt_execution_settings():
    settings = OllamaPromptExecutionSettings()

    assert settings.format is None
    assert settings.options is None


def test_custom_ollama_prompt_execution_settings():
    settings = OllamaPromptExecutionSettings(
        format="json",
        options={
            "key": "value",
        },
    )

    assert settings.format == "json"
    assert settings.options == {"key": "value"}


def test_ollama_prompt_execution_settings_from_default_completion_config():
    settings = PromptExecutionSettings(service_id="test_service")
    chat_settings = OllamaChatPromptExecutionSettings.from_prompt_execution_settings(settings)

    assert chat_settings.service_id == "test_service"
    assert chat_settings.format is None
    assert chat_settings.options is None


def test_ollama_prompt_execution_settings_from_openai_prompt_execution_settings():
    chat_settings = OllamaChatPromptExecutionSettings(service_id="test_service", options={"temperature": 0.5})
    new_settings = OllamaPromptExecutionSettings(service_id="test_2", options={"temperature": 0.0})
    chat_settings.update_from_prompt_execution_settings(new_settings)

    assert chat_settings.service_id == "test_2"
    assert chat_settings.options["temperature"] == 0.0


def test_ollama_prompt_execution_settings_from_custom_completion_config():
    settings = PromptExecutionSettings(
        service_id="test_service",
        extension_data={
            "format": "json",
            "options": {
                "key": "value",
            },
        },
    )
    chat_settings = OllamaChatPromptExecutionSettings.from_prompt_execution_settings(settings)

    assert chat_settings.service_id == "test_service"
    assert chat_settings.format == "json"
    assert chat_settings.options == {"key": "value"}


def test_ollama_chat_prompt_execution_settings_from_custom_completion_config_with_functions():
    settings = PromptExecutionSettings(
        service_id="test_service",
        extension_data={
            "tools": [{"function": {}}],
        },
    )
    chat_settings = OllamaChatPromptExecutionSettings.from_prompt_execution_settings(settings)

    assert chat_settings.tools == [{"function": {}}]


def test_create_options():
    settings = OllamaChatPromptExecutionSettings(
        service_id="test_service",
        extension_data={
            "format": "json",
        },
    )
    options = settings.prepare_settings_dict()

    assert options["format"] == "json"


def test_default_ollama_text_prompt_execution_settings():
    settings = OllamaTextPromptExecutionSettings()

    assert settings.system is None
    assert settings.template is None
    assert settings.context is None
    assert settings.raw is None
