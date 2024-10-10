# Copyright (c) Microsoft. All rights reserved.

import os
import sys

import pytest

from semantic_kernel.functions.kernel_arguments import KernelArguments

pytestmark = [
    pytest.mark.skipif(sys.version_info < (3, 9), reason="Google Palm requires Python 3.9 or greater"),
    pytest.mark.skipif(
        "Python_Integration_Tests" in os.environ,
        reason="Google Palm integration tests are only set up to run locally",
    ),
]


@pytest.mark.asyncio
async def test_text2text_generation_input_str(setup_gp_text_completion_function):
    kernel, text2text_function, simple_input = setup_gp_text_completion_function

    arguments = KernelArguments(input=simple_input, input2="")

    # Complete input string and print
    summary = await kernel.invoke(text2text_function, arguments)

    output = str(summary).strip()
    print(f"Completion using input string: '{output}'")
    assert len(output) > 0


@pytest.mark.asyncio
async def test_text2text_generation_empty_input_arguments(setup_gp_text_completion_function):
    kernel, text2text_function, simple_input = setup_gp_text_completion_function

    arguments = KernelArguments(input=simple_input, input2="")
    summary = await kernel.invoke(text2text_function, arguments)

    output = str(summary).strip()
    print(f"Completion using arguments: '{output}'")
    assert len(output) > 0


@pytest.mark.asyncio
async def test_text2text_generation_input_arguments_provided(setup_gp_text_completion_function):
    kernel, text2text_function, simple_input = setup_gp_text_completion_function

    arguments = KernelArguments(input=simple_input, input2="running and")
    summary = await kernel.invoke(text2text_function, arguments)

    output = str(summary).strip()
    print(f"Completion using input arguments: '{output}'")
    assert len(output) > 0
