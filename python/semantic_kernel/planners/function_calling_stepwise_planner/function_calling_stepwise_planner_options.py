# Copyright (c) Microsoft. All rights reserved.

from typing import Any, Callable, Optional

from pydantic import model_validator

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIPromptExecutionSettings,
)
from semantic_kernel.planners.planner_options import PlannerOptions


class FunctionCallingStepwisePlannerOptions(PlannerOptions):
    """The Function Calling Stepwise Planner Options."""

    max_tokens: Optional[int] = None
    max_tokens_ratio: Optional[float] = 0.1
    max_completion_tokens: Optional[int] = None
    max_prompt_tokens: Optional[int] = None
    get_initial_plan: Optional[Callable[[], str]] = None
    get_step_prompt: Optional[Callable[[], str]] = None
    max_iterations: Optional[int] = 15
    min_iteration_time_ms: Optional[int] = 100
    execution_settings: Optional[OpenAIPromptExecutionSettings] = None

    @model_validator(mode="before")
    @classmethod
    def calculate_token_limits(cls, data: Any) -> Any:
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
