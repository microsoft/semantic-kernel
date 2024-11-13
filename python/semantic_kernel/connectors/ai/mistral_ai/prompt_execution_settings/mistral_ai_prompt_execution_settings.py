# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from typing import Any, Literal

from mistralai import utils

if sys.version_info >= (3, 11):
    pass  # pragma: no cover
else:
    pass  # pragma: no cover

from pydantic import Field, field_validator

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings

logger = logging.getLogger(__name__)


class MistralAIPromptExecutionSettings(PromptExecutionSettings):
    """Common request settings for MistralAI services."""

    ai_model_id: str | None = Field(None, serialization_alias="model")


class MistralAIChatPromptExecutionSettings(MistralAIPromptExecutionSettings):
    """Specific settings for the Chat Completion endpoint."""

    response_format: dict[Literal["type"], Literal["text", "json_object"]] | None = None
    messages: list[dict[str, Any]] | None = None
    safe_mode: bool = Field(False, exclude=True)
    safe_prompt: bool = False
    max_tokens: int | None = Field(None, gt=0)
    seed: int | None = None
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    top_p: float | None = Field(None, ge=0.0, le=1.0)
    random_seed: int | None = None
    presence_penalty: float | None = Field(None, gt=0)
    frequency_penalty: float | None = Field(None, gt=0)
    n: int | None = Field(None, gt=1)
    retries: utils.RetryConfig | None = None
    server_url: str | None = None
    timeout_ms: int | None = None
    tools: list[dict[str, Any]] | None = Field(
        None,
        max_length=64,
        description="Do not set this manually. It is set by the service based on the function choice configuration.",
    )
    tool_choice: str | None = Field(
        None,
        description="Do not set this manually. It is set by the service based on the function choice configuration.",
    )

    @field_validator("safe_mode")
    @classmethod
    def check_safe_mode(cls, v: bool) -> bool:
        """The safe_mode setting is no longer supported."""
        logger.warning(
            "The 'safe_mode' setting is no longer supported and is being ignored, it will be removed in the Future."
        )
        return v
