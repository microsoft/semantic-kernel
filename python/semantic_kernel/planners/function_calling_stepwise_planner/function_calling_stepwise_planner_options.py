# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Callable
from typing import Any

from pydantic import model_validator

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIPromptExecutionSettings,
)
from semantic_kernel.planners.planner_options import PlannerOptions


class FunctionCallingStepwisePlannerOptions(PlannerOptions):
    """The Function Calling Stepwise Planner Options."""

    max_tokens: int | None = None
    max_tokens_ratio: float | None = 0.1
    max_completion_tokens: int | None = None
    max_prompt_tokens: int | None = None
    get_initial_plan: Callable[[], str] | None = None
    get_step_prompt: Callable[[], str] | None = None
    max_iterations: int | None = 15
    min_iteration_time_ms: int | None = 100
    execution_settings: OpenAIPromptExecutionSettings | None = None

    @model_validator(mode="before")
    @classmethod
    def calculate_token_limits(cls, data: Any) -> Any:
        """Calculate the token limits based on the max_tokens and max_tokens_ratio."""
        if isinstance(data, dict):
            max_tokens = data.get("max_tokens")
            # Ensure max_tokens_ratio has a default value if not provided
            max_tokens_ratio = data.get("max_tokens_ratio", 0.1)

            if max_tokens is not None:
                data["max_completion_tokens"] = int(max_tokens * max_tokens_ratio)
                data["max_prompt_tokens"] = int(max_tokens * (1 - max_tokens_ratio))
            else:
                # Explicitly setting them to None if max_tokens is None, for clarity
                data["max_completion_tokens"] = None
                data["max_prompt_tokens"] = None

        return data
