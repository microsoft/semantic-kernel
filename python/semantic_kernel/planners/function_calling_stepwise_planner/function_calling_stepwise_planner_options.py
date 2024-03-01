# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIPromptExecutionSettings,
)
from semantic_kernel.planners.planner_options import PlannerOptions

from typing import Any, Callable, Optional
from pydantic import model_validator, validator


class FunctionCallingStepwisePlannerOptions(PlannerOptions):
    max_tokens: Optional[int] = None
    max_tokens_ratio: Optional[int] = 0.1
    max_completion_tokens: Optional[int] = None
    max_prompt_tokens: Optional[int] = None
    get_initial_plan: Optional[Callable[[], str]] = None
    get_step_prompt: Optional[Callable[[str], str]] = None
    max_iterations: Optional[int] = 15
    min_iteration_time_ms: Optional[int] = 100
    execution_settings: Optional[OpenAIPromptExecutionSettings] = None

    @validator("max_prompt_tokens", always=True, pre=True)
    def configure_token_settings(cls, v, values, **kwargs):
        max_tokens = values.get("max_tokens")
        max_tokens_ratio = values.get("max_tokens_ratio", 0.1)  # Default to 0.1 if not provided
        if max_tokens is not None:
            values["max_tokens"] = max_tokens * max_tokens_ratio
        max_prompt_tokens = values.get("max_prompt_tokens")
        if max_prompt_tokens is not None:
            return max_tokens * (1 - max_tokens_ratio)
        return v
