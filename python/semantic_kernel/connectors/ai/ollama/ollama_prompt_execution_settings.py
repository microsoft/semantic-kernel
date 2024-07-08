# Copyright (c) Microsoft. All rights reserved.

from typing import Any, Literal

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


class OllamaPromptExecutionSettings(PromptExecutionSettings):
    format: Literal["json"] | None = None
    options: dict[str, Any] | None = None
    stream: bool = False


class OllamaTextPromptExecutionSettings(OllamaPromptExecutionSettings):
    prompt: str | None = None
    context: str | None = None
    system: str | None = None
    template: str | None = None
    raw: bool = False


class OllamaChatPromptExecutionSettings(OllamaPromptExecutionSettings):
    messages: list[dict[str, str]] | None = None
