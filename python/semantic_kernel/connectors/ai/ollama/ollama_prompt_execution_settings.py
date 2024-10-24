# Copyright (c) Microsoft. All rights reserved.

from typing import Any, Literal

from pydantic import Field

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


class OllamaPromptExecutionSettings(PromptExecutionSettings):
    """Settings for Ollama prompt execution."""

    format: Literal["json"] | None = None
    options: dict[str, Any] | None = None

    # TODO(@taochen): Add individual properties for execution settings and
    # convert them to the appropriate types in the options dictionary.


class OllamaTextPromptExecutionSettings(OllamaPromptExecutionSettings):
    """Settings for Ollama text prompt execution."""

    system: str | None = None
    template: str | None = None
    context: str | None = None
    raw: bool | None = None


class OllamaChatPromptExecutionSettings(OllamaPromptExecutionSettings):
    """Settings for Ollama chat prompt execution."""

    tools: list[dict[str, Any]] | None = Field(
        None,
        max_length=64,
        description="Do not set this manually. It is set by the service based on the function choice configuration.",
    )


class OllamaEmbeddingPromptExecutionSettings(OllamaPromptExecutionSettings):
    """Settings for Ollama embedding prompt execution."""
