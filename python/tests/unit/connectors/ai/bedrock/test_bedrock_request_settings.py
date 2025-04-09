# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.connectors.ai.bedrock import BedrockChatPromptExecutionSettings, BedrockPromptExecutionSettings
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


def test_default_bedrock_prompt_execution_settings():
    settings = BedrockPromptExecutionSettings()

    assert settings.temperature is None
    assert settings.top_p is None
    assert settings.top_k is None
    assert settings.max_tokens is None
    assert settings.stop == []


def test_custom_bedrock_prompt_execution_settings():
    settings = BedrockPromptExecutionSettings(
        temperature=0.5,
        top_p=0.5,
        top_k=10,
        max_tokens=128,
        stop=["world"],
    )

    assert settings.temperature == 0.5
    assert settings.top_p == 0.5
    assert settings.top_k == 10
    assert settings.max_tokens == 128
    assert settings.stop == ["world"]


def test_bedrock_prompt_execution_settings_from_default_completion_config():
    settings = PromptExecutionSettings(service_id="test_service")
    chat_settings = BedrockChatPromptExecutionSettings.from_prompt_execution_settings(settings)

    assert chat_settings.service_id == "test_service"
    assert chat_settings.temperature is None
    assert chat_settings.top_p is None
    assert chat_settings.top_k is None
    assert chat_settings.max_tokens is None
    assert chat_settings.stop == []


def test_bedrock_prompt_execution_settings_from_openai_prompt_execution_settings():
    chat_settings = BedrockChatPromptExecutionSettings(service_id="test_service", temperature=1.0)
    new_settings = BedrockPromptExecutionSettings(service_id="test_2", temperature=0.0)
    chat_settings.update_from_prompt_execution_settings(new_settings)

    assert chat_settings.service_id == "test_2"
    assert chat_settings.temperature == 0.0


def test_bedrock_prompt_execution_settings_from_custom_completion_config():
    settings = PromptExecutionSettings(
        service_id="test_service",
        extension_data={
            "temperature": 0.5,
            "top_p": 0.5,
            "top_k": 10,
            "max_tokens": 128,
            "stop": ["world"],
        },
    )
    chat_settings = BedrockChatPromptExecutionSettings.from_prompt_execution_settings(settings)

    assert chat_settings.temperature == 0.5
    assert chat_settings.top_p == 0.5
    assert chat_settings.top_k == 10
    assert chat_settings.max_tokens == 128
    assert chat_settings.stop == ["world"]


def test_bedrock_chat_prompt_execution_settings_from_custom_completion_config_with_functions():
    settings = PromptExecutionSettings(
        service_id="test_service",
        extension_data={
            "tools": [{"function": {}}],
        },
    )
    chat_settings = BedrockChatPromptExecutionSettings.from_prompt_execution_settings(settings)

    assert chat_settings.tools == [{"function": {}}]


def test_create_options():
    settings = BedrockPromptExecutionSettings(
        service_id="test_service",
        extension_data={
            "temperature": 0.5,
            "top_p": 0.5,
            "top_k": 10,
            "max_tokens": 128,
            "stop": ["world"],
        },
    )
    options = settings.prepare_settings_dict()

    assert options["temperature"] == 0.5
    assert options["top_p"] == 0.5
    assert options["top_k"] == 10
    assert options["max_tokens"] == 128
    assert options["stop"] == ["world"]
