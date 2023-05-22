# Copyright (c) Microsoft. All rights reserved.

import pytest

import semantic_kernel as sk


@pytest.mark.asyncio
async def test_summarize_input_str(setup_summarize_function):
    (
        kernel,
        summarize_function,
        text_to_summarize,
        additional_text,
    ) = setup_summarize_function

    # Summarize input string and print
    summary = await kernel.run_async(summarize_function, input_str=text_to_summarize)

    output = str(summary).strip()
    print(f"Summary using input string: '{output}'")
    assert len(output) > 0


@pytest.mark.asyncio
async def test_summarize_input_vars(setup_summarize_function):
    (
        kernel,
        summarize_function,
        text_to_summarize,
        additional_text,
    ) = setup_summarize_function

    # Summarize input as context variable and print
    context_vars = sk.ContextVariables(text_to_summarize)
    summary = await kernel.run_async(summarize_function, input_vars=context_vars)

    output = str(summary).strip()
    print(f"Summary using context variables: '{output}'")
    assert len(output) > 0


@pytest.mark.asyncio
async def test_summarize_input_context(setup_summarize_function):
    (
        kernel,
        summarize_function,
        text_to_summarize,
        additional_text,
    ) = setup_summarize_function

    # Summarize input context and print
    context = kernel.create_new_context()
    context["input"] = text_to_summarize
    summary = await kernel.run_async(summarize_function, input_context=context)

    output = str(summary).strip()
    print(f"Summary using input context: '{output}'")
    assert len(output) > 0


@pytest.mark.asyncio
async def test_summarize_input_context_with_vars(setup_summarize_function):
    (
        kernel,
        summarize_function,
        text_to_summarize,
        additional_text,
    ) = setup_summarize_function

    # Summarize input context with additional variables and print
    context = kernel.create_new_context()
    context["input"] = text_to_summarize
    context_vars = sk.ContextVariables(additional_text)
    summary = await kernel.run_async(
        summarize_function, input_context=context, input_vars=context_vars
    )

    output = str(summary).strip()
    print(f"Summary using context and additional variables: '{output}'")
    assert len(output) > 0


@pytest.mark.asyncio
async def test_summarize_input_context_with_str(setup_summarize_function):
    (
        kernel,
        summarize_function,
        text_to_summarize,
        additional_text,
    ) = setup_summarize_function

    # Summarize input context with additional input string and print
    context = kernel.create_new_context()
    context["input"] = text_to_summarize
    summary = await kernel.run_async(
        summarize_function, input_context=context, input_str=additional_text
    )

    output = str(summary).strip()
    print(f"Summary using context and additional string: '{output}'")
    assert len(output) > 0


@pytest.mark.asyncio
async def test_summarize_input_context_with_vars_and_str(setup_summarize_function):
    (
        kernel,
        summarize_function,
        text_to_summarize,
        additional_text,
    ) = setup_summarize_function

    # Summarize input context with additional variables and string and print
    context = kernel.create_new_context()
    context["input"] = text_to_summarize
    context_vars = sk.ContextVariables(variables={"input2": additional_text})
    summary = await kernel.run_async(
        summarize_function,
        input_context=context,
        input_vars=context_vars,
        input_str="new text",
    )

    output = str(summary).strip()
    print(
        f"Summary using context, additional variables, and additional string: '{output}'"
    )
    assert len(output) > 0
