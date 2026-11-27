# Copyright (c) Microsoft. All rights reserved.
import pytest
from pydantic import ValidationError

from semantic_kernel.connectors.ai.onnx.onnx_gen_ai_prompt_execution_settings import (
    OnnxGenAIPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


def test_default_onnx_chat_prompt_execution_settings():
    settings = OnnxGenAIPromptExecutionSettings()
    assert settings.temperature is None
    assert settings.top_p is None


def test_custom_onnx_chat_prompt_execution_settings():
    settings = OnnxGenAIPromptExecutionSettings(
        temperature=0.5,
        top_p=0.5,
        max_length=128,
    )
    assert settings.temperature == 0.5
    assert settings.top_p == 0.5
    assert settings.max_length == 128


def test_onnx_chat_prompt_execution_settings_from_default_completion_config():
    settings = PromptExecutionSettings(service_id="test_service")
    chat_settings = OnnxGenAIPromptExecutionSettings.from_prompt_execution_settings(settings)
    assert chat_settings.service_id == "test_service"
    assert chat_settings.temperature is None
    assert chat_settings.top_p is None


def test_onnx_chat_prompt_execution_settings_from_onnx_prompt_execution_settings():
    chat_settings = OnnxGenAIPromptExecutionSettings(service_id="test_service", temperature=1.0)
    new_settings = OnnxGenAIPromptExecutionSettings(service_id="test_2", temperature=0.0)
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
    chat_settings = OnnxGenAIPromptExecutionSettings.from_prompt_execution_settings(settings)
    assert chat_settings.temperature == 0.5
    assert chat_settings.top_p == 0.5
    assert chat_settings.max_length == 128


def test_create_options():
    settings = OnnxGenAIPromptExecutionSettings(
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
        OnnxGenAIPromptExecutionSettings(
            service_id="test_service",
            function_choice_behavior="auto",
            extension_data={
                "temperature": 10.0,
                "top_p": 0.5,
                "max_length": 128,
            },
        )


@pytest.mark.parametrize("repetition_penalty", [0.5, 1.0, 1.1, 1.5, 2.0])
def test_repetition_penalty_accepts_positive_values(repetition_penalty: float):
    # onnxruntime-genai: 1.0 means no penalty, values above 1.0 penalize repeated tokens.
    settings = OnnxGenAIPromptExecutionSettings(repetition_penalty=repetition_penalty)
    assert settings.prepare_settings_dict()["repetition_penalty"] == repetition_penalty


@pytest.mark.parametrize("repetition_penalty", [0.0, -1.0])
def test_repetition_penalty_rejects_non_positive_values(repetition_penalty: float):
    # The penalty divides positive logits, so it must be greater than 0.
    with pytest.raises(ValidationError):
        OnnxGenAIPromptExecutionSettings(repetition_penalty=repetition_penalty)


@pytest.mark.parametrize("length_penalty", [-1.0, -0.5, 0.0, 1.0, 1.5, 2.0])
def test_length_penalty_accepts_values_outside_zero_one(length_penalty: float):
    # onnxruntime-genai uses length_penalty as an exponent in beam search: > 0.0 promotes longer
    # sequences, < 0.0 promotes shorter ones.
    settings = OnnxGenAIPromptExecutionSettings(length_penalty=length_penalty)
    assert settings.prepare_settings_dict()["length_penalty"] == length_penalty
