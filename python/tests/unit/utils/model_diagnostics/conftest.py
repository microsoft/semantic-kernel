# Copyright (c) Microsoft. All rights reserved.


import sys
from collections.abc import AsyncGenerator
from typing import Any, ClassVar

import pytest

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

import semantic_kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.utils.telemetry.model_diagnostics.model_diagnostics_settings import ModelDiagnosticSettings


@pytest.fixture()
def model_diagnostics_unit_test_env(monkeypatch):
    """Fixture to set environment variables for Model Diagnostics Unit Tests."""
    env_vars = {
        "SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS": "true",
        "SEMANTICKERNEL_EXPERIMENTAL_GENAI_ENABLE_OTEL_DIAGNOSTICS_SENSITIVE": "true",
    }

    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    # Need to reload the settings to pick up the new environment variables since the
    # settings are loaded at import time and this fixture is called after the import
    semantic_kernel.utils.telemetry.model_diagnostics.decorators.MODEL_DIAGNOSTICS_SETTINGS = ModelDiagnosticSettings()


@pytest.fixture()
def service_env_vars(monkeypatch, request):
    """Fixture to set environment variables for AI Service Unit Tests."""
    for key, value in request.param.items():
        monkeypatch.setenv(key, value)


class MockChatCompletion(ChatCompletionClientBase):
    MODEL_PROVIDER_NAME: ClassVar[str] = "mock"

    @override
    async def _inner_get_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> list["ChatMessageContent"]:
        return []

    @override
    async def _inner_get_streaming_chat_message_contents(
        self,
        chat_history: "ChatHistory",
        settings: "PromptExecutionSettings",
    ) -> AsyncGenerator[list["StreamingChatMessageContent"], Any]:
        yield []

    @override
    def service_url(self) -> str | None:
        return "http://mock-service-url"


class MockTextCompletion(TextCompletionClientBase):
    MODEL_PROVIDER_NAME: ClassVar[str] = "mock"

    @override
    async def _inner_get_text_contents(
        self,
        prompt: str,
        settings: "PromptExecutionSettings",
    ) -> list["TextContent"]:
        return []

    @override
    async def _inner_get_streaming_text_contents(
        self,
        prompt: str,
        settings: "PromptExecutionSettings",
    ) -> AsyncGenerator[list["StreamingTextContent"], Any]:
        yield []

    @override
    def service_url(self) -> str | None:
        # Returning None to test the case where the service URL is not available
        return None
