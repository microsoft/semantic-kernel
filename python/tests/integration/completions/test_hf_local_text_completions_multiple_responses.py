# Copyright (c) Microsoft. All rights reserved.

import pytest
import random
from transformers import AutoTokenizer

import semantic_kernel as sk
import semantic_kernel.connectors.ai.hugging_face as sk_hf


@pytest.mark.asyncio
async def test_text2text_generation_input_str_multiple(setup_hf_text_completion_function_multiple_response):
    kernel, text2text_function, simple_input, n_responses = setup_hf_text_completion_function_multiple_response

    # Complete input string and print
    summary = await kernel.run_async(text2text_function, input_str=simple_input)

    output = str(summary)
    print(f"Completion using input string: '{output}'")
    print(f'n_responses : {n_responses}'+'num_resp : ',{output.count('\n')})
    assert len(output) > 0 and output.count('\n')==n_responses-1


@pytest.mark.asyncio
async def test_text2text_generation_input_vars_multiple(setup_hf_text_completion_function_multiple_response):
    kernel, text2text_function, simple_input, n_responses = setup_hf_text_completion_function_multiple_response

    # Complete input as context variable and print
    context_vars = sk.ContextVariables(simple_input)
    summary = await kernel.run_async(text2text_function, input_vars=context_vars)

    output = str(summary)
    print(f"Completion using context variables: '{output}'")
    print(f'n_responses : {n_responses}'+'num_resp : ',{output.count('\n')})
    assert len(output) > 0 and output.count('\n')==n_responses-1

@pytest.mark.asyncio
async def test_text2text_generation_input_context_multiple(setup_hf_text_completion_function_multiple_response):
    kernel, text2text_function, simple_input, n_responses = setup_hf_text_completion_function_multiple_response

    # Complete input context and print
    context = kernel.create_new_context()
    context["input"] = simple_input
    summary = await kernel.run_async(text2text_function, input_context=context)

    output = str(summary)
    print(f"Completion using input context: '{output}'")
    print(f'n_responses : {n_responses}'+'num_resp : ',{output.count('\n')})
    assert len(output) > 0 and output.count('\n')==n_responses-1

@pytest.mark.asyncio
async def test_text2text_generation_input_context_with_vars_multiple(
    setup_hf_text_completion_function_multiple_response,
):
    kernel, text2text_function, simple_input, n_responses = setup_hf_text_completion_function_multiple_response

    # Complete input context with additional variables and print
    context = kernel.create_new_context()
    context["input"] = simple_input
    context_vars = sk.ContextVariables("running and")
    summary = await kernel.run_async(
        text2text_function, input_context=context, input_vars=context_vars
    )

    output = str(summary)
    print(f"Completion using context and additional variables: '{output}'")
    print(f'n_responses : {n_responses}'+'num_resp : ',{output.count('\n')})
    assert len(output) > 0 and output.count('\n')==n_responses-1

@pytest.mark.asyncio
async def test_text2text_generation_input_context_with_str_multiple(
    setup_hf_text_completion_function_multiple_response,
):
    kernel, text2text_function, simple_input, n_responses = setup_hf_text_completion_function_multiple_response

    # Complete input context with additional input string and print
    context = kernel.create_new_context()
    context["input"] = simple_input
    summary = await kernel.run_async(
        text2text_function, input_context=context, input_str="running and"
    )

    output = str(summary)
    print(f"Completion using context and additional string: '{output}'")
    print(f'n_responses : {n_responses}'+'num_resp : ',{output.count('\n')})
    assert len(output) > 0 and output.count('\n')==n_responses-1

@pytest.mark.asyncio
async def test_text2text_generation_input_context_with_vars_and_str_multiple(
    setup_hf_text_completion_function_multiple_response,
):
    kernel, text2text_function, simple_input, n_responses = setup_hf_text_completion_function_multiple_response

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

    output = str(summary)
    print(
        f"Completion using context, additional variables, and additional string: '{output}'"
    )
    print(f'n_responses : {n_responses}'+'num_resp : ',{output.count('\n')})
    assert len(output) > 0 and output.count('\n')==n_responses-1

@pytest.mark.asyncio
async def test_text_generation_with_kwargs():
    simple_input = "sleeping and "
    model_name = "facebook/bart-large-cnn"

    tokenizer = AutoTokenizer.from_pretrained(
        pretrained_model_name_or_path=model_name, trust_remote_code=True
    )

    hf_model = sk_hf.HuggingFaceTextCompletion(
        model_name,
        task="text2text-generation",
        model_kwargs={"repetition_penalty": 0.2},
        pipeline_kwargs={"tokenizer": tokenizer, "trust_remote_code": True},
    )

    kernel = sk.Kernel()

    # Configure LLM service
    kernel.add_text_completion_service("hf-local", hf_model)

    # Define semantic function using SK prompt template language
    sk_prompt = "Hello, I like {{$input}}{{$input2}}"
    num_of_responses = random.randint(1,5)
    text2text_function = kernel.create_semantic_function(
        sk_prompt, max_tokens=25, temperature=0.2, top_p=0.5, number_of_responses=num_of_responses
    )

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
    assert len(output) > 0 and output.count('\n')==num_of_responses-1