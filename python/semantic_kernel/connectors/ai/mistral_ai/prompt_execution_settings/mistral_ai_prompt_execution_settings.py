# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from typing import Any, Literal

if sys.version_info >= (3, 11):
    from typing import Self  # pragma: no cover
else:
    from typing_extensions import Self  # pragma: no cover

from pydantic import Field, field_validator, model_validator

from semantic_kernel.connectors.ai.function_call_behavior import FunctionCallBehavior
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
    function_call_behavior: FunctionCallBehavior | None = Field(None, exclude=True)
    tools: list[dict[str, Any]] | None = Field(
        None,
        max_length=64,
        description="Do not set this manually. It is set by the service based on the function choice configuration.",
    )
    tool_choice: str | None = Field(
        None,
        description="Do not set this manually. It is set by the service based on the function choice configuration.",
    )
    
    @model_validator(mode="before")
    @classmethod
    def validate_function_calling_behaviors(cls, data) -> Any:
        """Check if function_call_behavior is set and if so, move to use function_choice_behavior instead."""
        # In an attempt to phase out the use of `function_call_behavior` in favor of `function_choice_behavior`,
        # we are syncing the `function_call_behavior` with `function_choice_behavior` if the former is set.
        # This allows us to make decisions off of `function_choice_behavior`. Anytime the `function_call_behavior`
        # is updated, this validation will run to ensure the `function_choice_behavior` stays in sync.
        from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior

        if isinstance(data, dict) and "function_call_behavior" in data.get("extension_data", {}):
            data["function_choice_behavior"] = FunctionChoiceBehavior.from_function_call_behavior(
                data.get("extension_data", {}).get("function_call_behavior")
            )
        return data

    @field_validator("function_call_behavior", mode="after")
    @classmethod
    def check_for_function_call_behavior(cls, v) -> Self:
        """Check if function_choice_behavior is set, if not, set it to default."""
        if v is not None:
            logger.warning(
                "The `function_call_behavior` parameter is deprecated. Please use the `function_choice_behavior` parameter instead."  # noqa: E501
            )
        return v

    
