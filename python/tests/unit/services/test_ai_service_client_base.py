# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.ai.prompt_execution_settings import (
    PromptExecutionSettings,
)
from semantic_kernel.services.ai_service_client_base import AIServiceClientBase


def test_init():
    service = AIServiceClientBase(service_id="service", ai_model_id="ai_model_id")
    assert service.service_id == "service"
    assert service.ai_model_id == "ai_model_id"


def test_init_no_service_id():
    service = AIServiceClientBase(ai_model_id="ai_model_id")
    assert service.service_id == "ai_model_id"
    assert service.ai_model_id == "ai_model_id"


def test_get_execution_settings_class():
    service = AIServiceClientBase(ai_model_id="ai_model_id")
    assert service.get_prompt_execution_settings_class() == PromptExecutionSettings


def test_instantiate_prompt_execution_settings():
    service = AIServiceClientBase(ai_model_id="ai_model_id")
    settings = service.instantiate_prompt_execution_settings(
        max_tokens=25, temperature=0.7, top_p=0.5
    )
    assert settings.extension_data["max_tokens"] == 25
    assert settings.extension_data["temperature"] == 0.7
    assert settings.extension_data["top_p"] == 0.5


def test_get_prompt_execution_settings_from_settings():
    service = AIServiceClientBase(ai_model_id="ai_model_id")
    settings = PromptExecutionSettings(
        service_id="service",
        extension_data={"max_tokens": 25, "temperature": 0.7, "top_p": 0.5},
    )
    new_settings = service.get_prompt_execution_settings_from_settings(settings)
    assert new_settings.extension_data["max_tokens"] == 25
    assert new_settings.extension_data["temperature"] == 0.7
    assert new_settings.extension_data["top_p"] == 0.5
    assert new_settings.service_id == settings.service_id
    assert new_settings.extension_data == settings.extension_data
