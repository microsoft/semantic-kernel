# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import OpenAIPromptExecutionSettings
from semantic_kernel.planners.planner_options import PlannerOptions

from typing import Any, Callable, Optional
from pydantic import model_validator

class FunctionCallingStepwisePlannerOptions(PlannerOptions, KernelBaseModel):

    max_tokens: Optional[int] = None
    max_tokens_ratio = Optional[int] = 0.1
    max_completion_tokens: Optional[int] = None
    max_prompt_tokens: Optional[int] = None
    get_initial_plan: Optional[Callable[[], str]] = None
    get_step_prompt: Optional[Callable[[str], str]] = None
    max_iterations: Optional[int] = 15
    min_iteration_time_ms = Optional[int] = None
    execution_settings: Optional[OpenAIPromptExecutionSettings] = None

    def __init__(
        self,
        max_tokens: Optional[int] = None,
        max_tokens_ratio: Optional[int] = 0.1,
        max_completion_tokens: Optional[int] = None,
        max_prompt_tokens: Optional[int] = None,
        get_initial_plan: Optional[Callable[[], str]] = None,
        get_step_prompt: Optional[Callable[[str], str]] = None,
        max_iterations: Optional[int] = 15,
        min_iteration_time_ms: Optional[int] = None,
        execution_settings: Optional[OpenAIPromptExecutionSettings] = None,
    ) -> None:
        super().__init(
            max_tokens=max_tokens,
            max_tokens_ratio=max_tokens_ratio,
            max_completion_tokens=max_completion_tokens,
            max_prompt_tokens=max_prompt_tokens,
            get_initial_plan=get_initial_plan,
            get_step_prompt=get_step_prompt,
            max_iterations=max_iterations,
            min_iteration_time_ms=min_iteration_time_ms,
            execution_settings=execution_settings,
        )

    @model_validator(mode="before")
    @classmethod
    def configure_token_settings(cls, fields: Any) -> Any:
        """Configure the token settings for the planner."""
        max_tokens = fields.get("max_tokens", None)
        max_tokens_ratio = fields.get("max_tokens_ratio", None)
        if max_tokens:
            fields["max_tokens"] = max_tokens * max_tokens_ratio
        max_prompt_tokens = fields.get("max_prompt_tokens", None)
        if max_prompt_tokens:
            fields["max_prompt_tokens"] = fields["max_tokens"] * (1 - max_tokens_ratio)
        return fields