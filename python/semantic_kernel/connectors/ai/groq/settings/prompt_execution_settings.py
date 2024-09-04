# Copyright (c) Microsoft. All rights reserved.

from typing import Any, Literal

from pydantic import Field, model_validator

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


class GroqPromptExecutionSettings(PromptExecutionSettings):
    """Settings for Groq prompt execution."""

    format: Literal["json"] | None = None
    options: dict[str, Any] | None = None


class GroqTextPromptExecutionSettings(GroqPromptExecutionSettings):
    """Settings for Groq text prompt execution."""


class GroqChatPromptExecutionSettings(GroqPromptExecutionSettings):
    """Specific settings for the Chat Completion endpoint."""

    messages: list[dict[str, Any]] | None = None
    stream: bool | None = None
    system: str | None = None
    max_tokens: int | None = Field(None, gt=0)
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    stop_sequences: list[str] | None = None
    top_p: float | None = Field(None, ge=0.0, le=1.0)
    top_k: int | None = Field(None, ge=0)

    @model_validator(mode="after")
    def check_function_call_behavior(self) -> "GroqChatPromptExecutionSettings":
        """Check if the user is requesting function call behavior."""
        if self.function_choice_behavior is not None:
            raise NotImplementedError("Anthropic does not support function call behavior.")

        return self


class GroqEmbeddingPromptExecutionSettings(GroqPromptExecutionSettings):
    """Settings for Groq embedding prompt execution."""
