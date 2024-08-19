# Copyright (c) Microsoft. All rights reserved.
import pytest
from pydantic import ValidationError

from semantic_kernel.connectors.ai.onnx import (
    OnnxTextPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


def test_default_onnx_chat_prompt_execution_settings():
    settings = OnnxTextPromptExecutionSettings()
    assert settings.temperature is None
    assert settings.top_p is None
    assert settings.max_length is None


def test_custom_onnx_chat_prompt_execution_settings():
    settings = OnnxTextPromptExecutionSettings(
        temperature=0.5,
        top_p=0.5,
        max_length=128,
    )
    assert settings.temperature == 0.5
    assert settings.top_p == 0.5
    assert settings.max_length == 128


def test_onnx_chat_prompt_execution_settings_from_default_completion_config():
    settings = PromptExecutionSettings(service_id="test_service")
    chat_settings = OnnxTextPromptExecutionSettings.from_prompt_execution_settings(settings)
    assert chat_settings.service_id == "test_service"
    assert chat_settings.temperature is None
    assert chat_settings.top_p is None
    assert chat_settings.max_length is None


def test_onnx_chat_prompt_execution_settings_from_onnx_prompt_execution_settings():
    chat_settings = OnnxTextPromptExecutionSettings(service_id="test_service", temperature=1.0)
    new_settings = OnnxTextPromptExecutionSettings(service_id="test_2", temperature=0.0)
    chat_settings.update_from_prompt_execution_settings(new_settings)
    assert chat_settings.service_id == "test_2"
    assert chat_settings.temperature == 0.0


def test_onnx_chat_prompt_execution_settings_from_custom_completion_config():
    settings = PromptExecutionSettings(
        service_id="test_service",
        extension_data={
            "temperature": 0.5,
            "top_p": 0.5,
            "max_length": 128,
        },
    )
    chat_settings = OnnxTextPromptExecutionSettings.from_prompt_execution_settings(settings)
    assert chat_settings.temperature == 0.5
    assert chat_settings.top_p == 0.5
    assert chat_settings.max_length == 128


def test_create_options():
    settings = OnnxTextPromptExecutionSettings(
        service_id="test_service",
        extension_data={
            "temperature": 0.5,
            "top_p": 0.5,
            "max_length": 128,
        },
    )
    options = settings.prepare_settings_dict()
    assert options["temperature"] == 0.5
    assert options["top_p"] == 0.5
    assert options["max_length"] == 128


def test_create_options_with_wrong_parameter():
    with pytest.raises(ValidationError):
        OnnxTextPromptExecutionSettings(
            service_id="test_service",
            function_choice_behavior="auto",
            extension_data={
                "temperature": 10.0,
                "top_p": 0.5,
                "max_length": 128,
            },
        )
