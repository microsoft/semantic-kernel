# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Any

from pydantic import Field, model_validator

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings

logger = logging.getLogger(__name__)


class AnthropicPromptExecutionSettings(PromptExecutionSettings):
    """Common request settings for Anthropic services."""

    ai_model_id: str | None = Field(None, serialization_alias="model")


class AnthropicChatPromptExecutionSettings(AnthropicPromptExecutionSettings):
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
    def check_function_call_behavior(self) -> "AnthropicChatPromptExecutionSettings":
        """Check if the user is requesting function call behavior."""
        if self.function_choice_behavior is not None:
            raise NotImplementedError("Anthropic does not support function call behavior.")
            
        return self
