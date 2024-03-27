# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

import pytest

from semantic_kernel.planners.function_calling_stepwise_planner.function_calling_stepwise_planner_options import (
    FunctionCallingStepwisePlannerOptions,
)


@pytest.mark.parametrize(
    "max_tokens, max_tokens_ratio, expected_max_completion, expected_max_prompt",
    [
        (100, 0.1, 10, 90),
        (200, 0.2, 40, 160),
        (None, 0.1, None, None),
    ],
)
def test_calculate_token_limits(max_tokens, max_tokens_ratio, expected_max_completion, expected_max_prompt):
    options_data = {"max_tokens": max_tokens, "max_tokens_ratio": max_tokens_ratio}
    options = FunctionCallingStepwisePlannerOptions(**options_data)

    assert (
        options.max_completion_tokens == expected_max_completion
    ), "max_completion_tokens did not match expected value"
    assert options.max_prompt_tokens == expected_max_prompt, "max_prompt_tokens did not match expected value"


def test_defaults():
    """Test that defaults are applied correctly when no values are provided."""
    options = FunctionCallingStepwisePlannerOptions()
    assert options.max_tokens_ratio == 0.1, "Default max_tokens_ratio not applied"
    assert options.max_iterations == 15, "Default max_iterations not applied"
    assert options.min_iteration_time_ms == 100, "Default min_iteration_time_ms not applied"
    assert options.max_completion_tokens is None, "max_completion_tokens should be None when max_tokens is not set"
    assert options.max_prompt_tokens is None, "max_prompt_tokens should be None when max_tokens is not set"


@pytest.mark.parametrize(
    "field",
    [
        ("get_initial_plan"),
        ("get_step_prompt"),
        ("execution_settings"),
    ],
)
def test_optional_fields_none_by_default(field):
    options = FunctionCallingStepwisePlannerOptions()
    assert getattr(options, field) is None, f"{field} should be None by default"
