# Copyright (c) Microsoft. All rights reserved.

import pytest
from pydantic import ValidationError

from semantic_kernel.connectors.ai.mistral_ai.prompt_execution_settings.mistral_ai_prompt_execution_settings import (
    MistralAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


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
    chat_settings = MistralAIChatPromptExecutionSettings.from_prompt_execution_settings(settings)
    assert chat_settings.service_id == "test_service"
    assert chat_settings.temperature is None
    assert chat_settings.top_p is None
    assert chat_settings.max_tokens is None


def test_mistral_chat_prompt_execution_settings_from_openai_prompt_execution_settings():
    chat_settings = MistralAIChatPromptExecutionSettings(service_id="test_service", temperature=1.0)
    new_settings = MistralAIChatPromptExecutionSettings(service_id="test_2", temperature=0.0)
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
    chat_settings = MistralAIChatPromptExecutionSettings.from_prompt_execution_settings(settings)
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
    chat_settings = MistralAIChatPromptExecutionSettings.from_prompt_execution_settings(settings)
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
    chat_settings = MistralAIChatPromptExecutionSettings.from_prompt_execution_settings(settings)
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


def test_prepare_settings_dict_maps_seed_to_random_seed():
    # The Mistral SDK has no `seed` parameter, only `random_seed`
    settings = MistralAIChatPromptExecutionSettings(seed=42)
    options = settings.prepare_settings_dict()
    assert "seed" not in options
    assert options["random_seed"] == 42


def test_prepare_settings_dict_keeps_explicit_random_seed():
    settings = MistralAIChatPromptExecutionSettings(seed=42, random_seed=7)
    options = settings.prepare_settings_dict()
    assert "seed" not in options
    assert options["random_seed"] == 7


@pytest.mark.parametrize("penalty_name", ["presence_penalty", "frequency_penalty"])
@pytest.mark.parametrize("value", [-2.0, -0.5, 0.0, 0.5, 2.0])
def test_penalties_accept_values_in_mistral_range(penalty_name: str, value: float):
    # The Mistral API accepts presence_penalty and frequency_penalty in [-2, 2], 0 means no penalty.
    settings = MistralAIChatPromptExecutionSettings(**{penalty_name: value})
    assert settings.prepare_settings_dict()[penalty_name] == value


@pytest.mark.parametrize("penalty_name", ["presence_penalty", "frequency_penalty"])
@pytest.mark.parametrize("value", [-2.1, 2.1])
def test_penalties_reject_values_outside_mistral_range(penalty_name: str, value: float):
    with pytest.raises(ValidationError):
        MistralAIChatPromptExecutionSettings(**{penalty_name: value})


@pytest.mark.parametrize("n", [1, 2])
def test_n_accepts_positive_values(n: int):
    settings = MistralAIChatPromptExecutionSettings(n=n)
    assert settings.prepare_settings_dict()["n"] == n


def test_n_rejects_zero():
    with pytest.raises(ValidationError):
        MistralAIChatPromptExecutionSettings(n=0)


def test_from_prompt_execution_settings_with_zero_penalties():
    settings = PromptExecutionSettings(
        service_id="test_service",
        extension_data={"max_tokens": 256, "presence_penalty": 0, "frequency_penalty": 0, "n": 1},
    )
    chat_settings = MistralAIChatPromptExecutionSettings.from_prompt_execution_settings(settings)
    assert chat_settings.presence_penalty == 0
    assert chat_settings.frequency_penalty == 0
    assert chat_settings.n == 1
