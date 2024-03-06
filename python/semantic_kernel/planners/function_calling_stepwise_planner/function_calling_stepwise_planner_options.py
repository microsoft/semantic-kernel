# Copyright (c) Microsoft. All rights reserved.

from typing import Callable, Optional

from pydantic import field_validator

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIPromptExecutionSettings,
)
from semantic_kernel.planners.planner_options import PlannerOptions


class FunctionCallingStepwisePlannerOptions(PlannerOptions):
    """The Function Calling Stepwise Planner Options."""

    max_tokens: Optional[int] = None
    max_tokens_ratio: Optional[int] = 0.1
    max_completion_tokens: Optional[int] = None
    max_prompt_tokens: Optional[int] = None
    get_initial_plan: Optional[Callable[[], str]] = None
    get_step_prompt: Optional[Callable[[], str]] = None
    max_iterations: Optional[int] = 15
    min_iteration_time_ms: Optional[int] = 100
    execution_settings: Optional[OpenAIPromptExecutionSettings] = None

    @field_validator('max_tokens', 'max_prompt_tokens', mode='after')
    @classmethod
    def adjust_token_settings(cls, value, info):
        max_tokens = info.data.get('max_tokens')
        max_tokens_ratio = info.data.get('max_tokens_ratio', 0.1)

        if max_tokens is not None and info.field_name == 'max_tokens':
            return int(max_tokens * max_tokens_ratio)
        elif max_tokens is not None and info.field_name == 'max_prompt_tokens':
            return int(max_tokens * (1 - max_tokens_ratio))
        
        return value
