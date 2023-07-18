# Copyright (c) Microsoft. All rights reserved.

import pytest
import semantic_kernel as sk


@pytest.mark.asyncio
async def test_text2text_generation_input_str(setup_gp_text_completion_function):
    kernel, text2text_function, simple_input = setup_gp_text_completion_function

    # Complete input string and print
    summary = await kernel.run_async(text2text_function, input_str=simple_input)

    output = str(summary).strip()
    print(f"Completion using input string: '{output}'")
    assert len(output) > 0


@pytest.mark.asyncio
async def test_text2text_generation_input_vars(setup_gp_text_completion_function):
    kernel, text2text_function, simple_input = setup_gp_text_completion_function

    # Complete input as context variable and print
    context_vars = sk.ContextVariables(simple_input)
    summary = await kernel.run_async(text2text_function, input_vars=context_vars)

    output = str(summary).strip()
    print(f"Completion using context variables: '{output}'")
    assert len(output) > 0


@pytest.mark.asyncio
async def test_text2text_generation_input_context(setup_gp_text_completion_function):
    kernel, text2text_function, simple_input = setup_gp_text_completion_function

    # Complete input context and print
    context = kernel.create_new_context()
    context["input"] = simple_input
    summary = await kernel.run_async(text2text_function, input_context=context)

    output = str(summary).strip()
    print(f"Completion using input context: '{output}'")
    assert len(output) > 0


@pytest.mark.asyncio
async def test_text2text_generation_input_context_with_vars(
    setup_gp_text_completion_function,
):
    kernel, text2text_function, simple_input = setup_gp_text_completion_function

    # Complete input context with additional variables and print
    context = kernel.create_new_context()
    context["input"] = simple_input
    context_vars = sk.ContextVariables("running and")
    summary = await kernel.run_async(
        text2text_function, input_context=context, input_vars=context_vars
    )

    output = str(summary).strip()
    print(f"Completion using context and additional variables: '{output}'")
    assert len(output) > 0


@pytest.mark.asyncio
async def test_text2text_generation_input_context_with_str(
    setup_gp_text_completion_function,
):
    kernel, text2text_function, simple_input = setup_gp_text_completion_function

    # Complete input context with additional input string and print
    context = kernel.create_new_context()
    context["input"] = simple_input
    summary = await kernel.run_async(
        text2text_function, input_context=context, input_str="running and"
    )

    output = str(summary).strip()
    print(f"Completion using context and additional string: '{output}'")
    assert len(output) > 0

@pytest.mark.asyncio
async def test_text2text_generation_input_context_with_vars_and_str(
    setup_gp_text_completion_function,
):
    kernel, text2text_function, simple_input = setup_gp_text_completion_function

    # Complete input context with additional variables and string and print
    context = kernel.create_new_context()
    context["input"] = simple_input
    context_vars = sk.ContextVariables(variables={"input2": "running and"})
    summary = await kernel.run_async(
        text2text_function,
        input_context=context,
        input_vars=context_vars,
        input_str="new text",
    )

    output = str(summary).strip()
    print(
        f"Completion using context, additional variables, and additional string: '{output}'"
    )
    assert len(output) > 0