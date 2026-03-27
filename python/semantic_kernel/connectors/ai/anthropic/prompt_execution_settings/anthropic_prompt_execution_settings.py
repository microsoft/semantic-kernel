# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Annotated, Any

from pydantic import Field, model_validator

from semantic_kernel.connectors.ai.function_choice_type import FunctionChoiceType
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.exceptions import ServiceInvalidExecutionSettingsError

logger = logging.getLogger(__name__)


class AnthropicPromptExecutionSettings(PromptExecutionSettings):
    """Common request settings for Anthropic services."""

    ai_model_id: Annotated[str | None, Field(serialization_alias="model")] = None


class AnthropicChatPromptExecutionSettings(AnthropicPromptExecutionSettings):
    """Specific settings for the Chat Completion endpoint."""

    messages: list[dict[str, Any]] | None = None
    stream: bool | None = None
    system: str | None = None
    max_tokens: Annotated[int, Field(gt=0)] = 1024
    temperature: Annotated[float | None, Field(ge=0.0, le=2.0)] = None
    stop_sequences: list[str] | None = None
    top_p: Annotated[float | None, Field(ge=0.0, le=1.0)] = None
    top_k: Annotated[int | None, Field(ge=0)] = None
    tools: Annotated[
        list[dict[str, Any]] | None,
        Field(
            description=(
                "Do not set this manually. It is set by the service based on the function choice configuration."
            ),
        ),
    ] = None
    tool_choice: Annotated[
        dict[str, str] | None,
        Field(
            description="Do not set this manually. It is set by the service based on the function choice configuration."
        ),
    ] = None

    @model_validator(mode="after")
    def validate_tool_choice(self) -> "AnthropicChatPromptExecutionSettings":
        """Validate tool choice payload.

        Anthropic supports disabling tool calls by setting {"type": "none"},
        which is used when auto-invocation attempts are exhausted.
        """
        if self.tool_choice is None:
            return self

        allowed_tool_choice_types = {
            FunctionChoiceType.AUTO.value,
            FunctionChoiceType.NONE.value,
            FunctionChoiceType.REQUIRED.value,
            "any",
            "tool",
        }
        tool_choice_type = self.tool_choice.get("type")
        if tool_choice_type not in allowed_tool_choice_types:
            raise ServiceInvalidExecutionSettingsError(
                f"Invalid Anthropic tool_choice type '{tool_choice_type}'. "
                f"Expected one of: {sorted(allowed_tool_choice_types)}."
            )
        return self
