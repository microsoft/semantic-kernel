# Copyright (c) Microsoft. All rights reserved.


import pytest

from semantic_kernel.kernel import Kernel
from semantic_kernel.planners.stepwise_planner.stepwise_planner import StepwisePlanner


@pytest.mark.parametrize(
    "input, expected",
    [
        ("[FINAL ANSWER] 42", "42"),
        ("[FINAL ANSWER]42", "42"),
        ("I think I have everything I need.\n[FINAL ANSWER] 42", "42"),
        ("I think I have everything I need.\n[FINAL ANSWER] 42\n", "42"),
        ("I think I have everything I need.\n[FINAL ANSWER] 42\n\n", "42"),
        ("I think I have everything I need.\n[FINAL ANSWER]42\n\n\n", "42"),
        ("I think I have everything I need.\n[FINAL ANSWER]\n 42\n\n\n", "42"),
    ],
)
def test_when_input_is_final_answer_returns_final_answer(kernel: Kernel, input: str, expected: str):
    # kernel.prompt_template_engine = Mock()
    planner = StepwisePlanner(kernel)

    result = planner.parse_result(input)

    assert result.final_answer == expected


@pytest.mark.parametrize(
    "input, expected",
    [
        ("My thought", "My thought"),
        ("My thought\n", "My thought"),
        ("My thought\n\n", "My thought"),
        ("My thought\n\n\n", "My thought"),
    ],
)
def test_when_input_is_only_thought_does_not_throw_error(kernel: Kernel, input: str, expected: str):
    planner = StepwisePlanner(kernel)
    result = planner.parse_result(input)
    assert result.thought == expected


if __name__ == "__main__":
    pytest.main([__file__])
