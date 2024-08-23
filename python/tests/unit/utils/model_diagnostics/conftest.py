# Copyright (c) Microsoft. All rights reserved.


import pytest

import semantic_kernel
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.utils.telemetry.model_diagnostics.model_diagnostics_settings import ModelDiagnosticSettings


@pytest.fixture()
def model_diagnostics_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for Model Diagnostics Unit Tests."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {
        "SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS": "true",
        "SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS_SENSITIVE": "true",
    }

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    # Need to reload the settings to pick up the new environment variables since the
    # settings are loaded at import time and this fixture is called after the import
    semantic_kernel.utils.telemetry.model_diagnostics.decorators.MODEL_DIAGNOSTICS_SETTINGS = (
        ModelDiagnosticSettings.create()
    )

    return env_vars


@pytest.fixture()
def mock_prompt_execution_settings() -> PromptExecutionSettings:
    return PromptExecutionSettings(
        extension_data={
            "max_tokens": 1000,
            "temperature": 0.5,
            "top_p": 0.9,
        }
    )


@pytest.fixture()
def mock_get_chat_message_contents_response() -> list[ChatMessageContent]:
    return [
        ChatMessageContent(
            role=AuthorRole.ASSISTANT,
            ai_model_id="ai_model_id",
            content="Test content",
            metadata={"id": "test_id"},
            finish_reason=FinishReason.STOP,
        )
    ]


@pytest.fixture()
def mock_get_text_contents_response() -> list[TextContent]:
    return [
        TextContent(
            ai_model_id="ai_model_id",
            text="Test content",
            metadata={"id": "test_id"},
        )
    ]
