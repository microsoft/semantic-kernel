# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from typing import Annotated, Any, Literal

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

    ai_model_id: Annotated[str | None, Field(serialization_alias="model")] = None


class MistralAIChatPromptExecutionSettings(MistralAIPromptExecutionSettings):
    """Specific settings for the Chat Completion endpoint."""

    response_format: dict[Literal["type"], Literal["text", "json_object"]] | None = None
    messages: list[dict[str, Any]] | None = None
    safe_mode: Annotated[bool, Field(exclude=True)] = False
    safe_prompt: bool = False
    max_tokens: Annotated[int | None, Field(gt=0)] = None
    seed: int | None = None
    temperature: Annotated[float | None, Field(ge=0.0, le=2.0)] = None
    top_p: Annotated[float | None, Field(ge=0.0, le=1.0)] = None
    random_seed: int | None = None
    presence_penalty: Annotated[float | None, Field(gt=0)] = None
    frequency_penalty: Annotated[float | None, Field(gt=0)] = None
    n: Annotated[int | None, Field(gt=1)] = None
    retries: utils.RetryConfig | None = None
    server_url: str | None = None
    timeout_ms: int | None = None
    tools: Annotated[
        list[dict[str, Any]] | None,
        Field(
            description="Do not set this manually. It is set by the service based "
            "on the function choice configuration.",
        ),
    ] = None
    tool_choice: Annotated[
        str | None,
        Field(
            description="Do not set this manually. It is set by the service based "
            "on the function choice configuration.",
        ),
    ] = None

    @field_validator("safe_mode")
    @classmethod
    def check_safe_mode(cls, v: bool) -> bool:
        """The safe_mode setting is no longer supported."""
        logger.warning(
            "The 'safe_mode' setting is no longer supported and is being ignored, it will be removed in the Future."
        )
        return v
