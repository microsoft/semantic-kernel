# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.ai.google.google_ai import (
    GoogleAIChatPromptExecutionSettings,
    GoogleAIEmbeddingPromptExecutionSettings,
    GoogleAIPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


def test_default_google_ai_prompt_execution_settings():
    settings = GoogleAIPromptExecutionSettings()

    assert settings.stop_sequences is None
    assert settings.response_mime_type is None
    assert settings.response_schema is None
    assert settings.candidate_count is None
    assert settings.max_output_tokens is None
    assert settings.temperature is None
    assert settings.top_p is None
    assert settings.top_k is None


def test_custom_google_ai_prompt_execution_settings():
    settings = GoogleAIPromptExecutionSettings(
        stop_sequences=["world"],
        response_mime_type="text/plain",
        candidate_count=1,
        max_output_tokens=128,
        temperature=0.5,
        top_p=0.5,
        top_k=10,
    )

    assert settings.stop_sequences == ["world"]
    assert settings.response_mime_type == "text/plain"
    assert settings.candidate_count == 1
    assert settings.max_output_tokens == 128
    assert settings.temperature == 0.5
    assert settings.top_p == 0.5
    assert settings.top_k == 10


def test_google_ai_prompt_execution_settings_from_default_completion_config():
    settings = PromptExecutionSettings(service_id="test_service")
    chat_settings = GoogleAIChatPromptExecutionSettings.from_prompt_execution_settings(settings)

    assert chat_settings.service_id == "test_service"
    assert chat_settings.stop_sequences is None
    assert chat_settings.response_mime_type is None
    assert chat_settings.response_schema is None
    assert chat_settings.candidate_count is None
    assert chat_settings.max_output_tokens is None
    assert chat_settings.temperature is None
    assert chat_settings.top_p is None
    assert chat_settings.top_k is None


def test_google_ai_prompt_execution_settings_from_openai_prompt_execution_settings():
    chat_settings = GoogleAIChatPromptExecutionSettings(service_id="test_service", temperature=1.0)
    new_settings = GoogleAIPromptExecutionSettings(service_id="test_2", temperature=0.0)
    chat_settings.update_from_prompt_execution_settings(new_settings)

    assert chat_settings.service_id == "test_2"
    assert chat_settings.temperature == 0.0


def test_google_ai_prompt_execution_settings_from_custom_completion_config():
    settings = PromptExecutionSettings(
        service_id="test_service",
        extension_data={
            "stop_sequences": ["world"],
            "response_mime_type": "text/plain",
            "candidate_count": 1,
            "max_output_tokens": 128,
            "temperature": 0.5,
            "top_p": 0.5,
            "top_k": 10,
        },
    )
    chat_settings = GoogleAIChatPromptExecutionSettings.from_prompt_execution_settings(settings)

    assert chat_settings.stop_sequences == ["world"]
    assert chat_settings.response_mime_type == "text/plain"
    assert chat_settings.candidate_count == 1
    assert chat_settings.max_output_tokens == 128
    assert chat_settings.temperature == 0.5
    assert chat_settings.top_p == 0.5
    assert chat_settings.top_k == 10


def test_google_ai_chat_prompt_execution_settings_from_custom_completion_config_with_functions():
    settings = PromptExecutionSettings(
        service_id="test_service",
        extension_data={
            "tools": [{"function": {}}],
        },
    )
    chat_settings = GoogleAIChatPromptExecutionSettings.from_prompt_execution_settings(settings)

    assert chat_settings.tools == [{"function": {}}]


def test_create_options():
    settings = GoogleAIChatPromptExecutionSettings(
        service_id="test_service",
        extension_data={
            "stop_sequences": ["world"],
            "response_mime_type": "text/plain",
            "candidate_count": 1,
            "max_output_tokens": 128,
            "temperature": 0.5,
            "top_p": 0.5,
            "top_k": 10,
        },
    )
    options = settings.prepare_settings_dict()

    assert options["stop_sequences"] == ["world"]
    assert options["response_mime_type"] == "text/plain"
    assert options["candidate_count"] == 1
    assert options["max_output_tokens"] == 128
    assert options["temperature"] == 0.5
    assert options["top_p"] == 0.5
    assert options["top_k"] == 10
    assert "tools" not in options
    assert "tool_config" not in options


def test_default_google_ai_embedding_prompt_execution_settings():
    settings = GoogleAIEmbeddingPromptExecutionSettings()

    assert settings.output_dimensionality is None
