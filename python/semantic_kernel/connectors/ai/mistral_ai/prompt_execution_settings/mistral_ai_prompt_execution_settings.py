# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Any, Literal

from pydantic import Field, model_validator

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings

logger = logging.getLogger(__name__)


class MistralAIPromptExecutionSettings(PromptExecutionSettings):
    """Common request settings for MistralAI services."""

    ai_model_id: str | None = Field(None, serialization_alias="model")


class MistralAIChatPromptExecutionSettings(MistralAIPromptExecutionSettings):
    """Specific settings for the Chat Completion endpoint."""

    response_format: dict[Literal["type"], Literal["text", "json_object"]] | None = None
    messages: list[dict[str, Any]] | None = None
    safe_mode: bool = False
    safe_prompt: bool = False
    max_tokens: int | None = Field(None, gt=0)
    seed: int | None = None
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    top_p: float | None = Field(None, ge=0.0, le=1.0)
    random_seed: int | None = None

    @model_validator(mode="after")
    def check_function_call_behavior(self) -> "MistralAIChatPromptExecutionSettings":
        """Check if the user is requesting function call behavior."""
        if self.function_choice_behavior is not None:
            raise NotImplementedError("MistralAI does not support function call behavior.")
            
        return self
