# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from semantic_kernel.prompt_template.input_variable import InputVariable
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


def _function_with_default(default: object) -> KernelFunctionFromPrompt:
    return KernelFunctionFromPrompt(
        function_name="test",
        prompt_template_config=PromptTemplateConfig(
            template="{{$input}}",
            input_variables=[InputVariable(name="input", default=default, is_required=False)],
        ),
    )


@pytest.mark.parametrize(
    ("default", "is_applied"),
    [
        (0, True),
        (False, True),
        ("", False),
        ("x", True),
        (None, False),
    ],
)
def test_update_arguments_with_defaults_applies_falsy_defaults(default: object, is_applied: bool):
    function = _function_with_default(default)
    arguments = KernelArguments()

    function.update_arguments_with_defaults(arguments)

    assert ("input" in arguments) is is_applied
    if is_applied:
        assert arguments["input"] == default


def test_update_arguments_with_defaults_does_not_override_explicit_argument():
    function = _function_with_default("default")
    arguments = KernelArguments(input="explicit")

    function.update_arguments_with_defaults(arguments)

    assert arguments["input"] == "explicit"
