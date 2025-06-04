# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.ai.azure_ai_inference import (
    AzureAIInferenceChatPromptExecutionSettings,
    AzureAIInferenceEmbeddingPromptExecutionSettings,
    AzureAIInferencePromptExecutionSettings,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


def test_default_azure_ai_inference_prompt_execution_settings():
    settings = AzureAIInferencePromptExecutionSettings()

    assert settings.frequency_penalty is None
    assert settings.max_tokens is None
    assert settings.presence_penalty is None
    assert settings.seed is None
    assert settings.stop is None
    assert settings.temperature is None
    assert settings.top_p is None
    assert settings.extra_parameters is None


def test_custom_azure_ai_inference_prompt_execution_settings():
    settings = AzureAIInferencePromptExecutionSettings(
        frequency_penalty=0.5,
        max_tokens=128,
        presence_penalty=0.5,
        seed=1,
        stop="world",
        temperature=0.5,
        top_p=0.5,
        extra_parameters={"key": "value"},
    )

    assert settings.frequency_penalty == 0.5
    assert settings.max_tokens == 128
    assert settings.presence_penalty == 0.5
    assert settings.seed == 1
    assert settings.stop == "world"
    assert settings.temperature == 0.5
    assert settings.top_p == 0.5
    assert settings.extra_parameters == {"key": "value"}


def test_azure_ai_inference_prompt_execution_settings_from_default_completion_config():
    settings = PromptExecutionSettings(service_id="test_service")
    chat_settings = AzureAIInferenceChatPromptExecutionSettings.from_prompt_execution_settings(settings)

    assert chat_settings.service_id == "test_service"
    assert chat_settings.frequency_penalty is None
    assert chat_settings.max_tokens is None
    assert chat_settings.presence_penalty is None
    assert chat_settings.seed is None
    assert chat_settings.stop is None
    assert chat_settings.temperature is None
    assert chat_settings.top_p is None
    assert chat_settings.extra_parameters is None


def test_azure_ai_inference_prompt_execution_settings_from_openai_prompt_execution_settings():
    chat_settings = AzureAIInferenceChatPromptExecutionSettings(service_id="test_service", temperature=1.0)
    new_settings = AzureAIInferencePromptExecutionSettings(service_id="test_2", temperature=0.0)
    chat_settings.update_from_prompt_execution_settings(new_settings)

    assert chat_settings.service_id == "test_2"
    assert chat_settings.temperature == 0.0


def test_azure_ai_inference_prompt_execution_settings_from_custom_completion_config():
    settings = PromptExecutionSettings(
        service_id="test_service",
        extension_data={
            "frequency_penalty": 0.5,
            "max_tokens": 128,
            "presence_penalty": 0.5,
            "seed": 1,
            "stop": "world",
            "temperature": 0.5,
            "top_p": 0.5,
            "extra_parameters": {"key": "value"},
        },
    )
    chat_settings = AzureAIInferenceChatPromptExecutionSettings.from_prompt_execution_settings(settings)

    assert chat_settings.service_id == "test_service"
    assert chat_settings.frequency_penalty == 0.5
    assert chat_settings.max_tokens == 128
    assert chat_settings.presence_penalty == 0.5
    assert chat_settings.seed == 1
    assert chat_settings.stop == "world"
    assert chat_settings.temperature == 0.5
    assert chat_settings.top_p == 0.5
    assert chat_settings.extra_parameters == {"key": "value"}


def test_azure_ai_inference_chat_prompt_execution_settings_from_custom_completion_config_with_functions():
    settings = PromptExecutionSettings(
        service_id="test_service",
        extension_data={
            "tools": [{"function": {}}],
        },
    )
    chat_settings = AzureAIInferenceChatPromptExecutionSettings.from_prompt_execution_settings(settings)

    assert chat_settings.tools == [{"function": {}}]


def test_create_options():
    settings = AzureAIInferenceChatPromptExecutionSettings(
        service_id="test_service",
        extension_data={
            "frequency_penalty": 0.5,
            "max_tokens": 128,
            "presence_penalty": 0.5,
            "seed": 1,
            "stop": "world",
            "temperature": 0.5,
            "top_p": 0.5,
            "extra_parameters": {"key": "value"},
        },
    )
    options = settings.prepare_settings_dict()

    assert options["frequency_penalty"] == 0.5
    assert options["max_tokens"] == 128
    assert options["presence_penalty"] == 0.5
    assert options["seed"] == 1
    assert options["stop"] == "world"
    assert options["temperature"] == 0.5
    assert options["top_p"] == 0.5
    assert options["extra_parameters"] == {"key": "value"}
    assert "tools" not in options
    assert "tool_config" not in options


def test_default_azure_ai_inference_embedding_prompt_execution_settings():
    settings = AzureAIInferenceEmbeddingPromptExecutionSettings()

    assert settings.dimensions is None
    assert settings.encoding_format is None
    assert settings.input_type is None
    assert settings.extra_parameters is None
