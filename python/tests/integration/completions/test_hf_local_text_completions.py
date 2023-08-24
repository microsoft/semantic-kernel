# Copyright (c) Microsoft. All rights reserved.

import pytest
import torch

import semantic_kernel as sk
import semantic_kernel.connectors.ai.hugging_face as sk_hf

from transformers import AutoTokenizer


@pytest.mark.asyncio
async def test_text2text_generation_input_str(setup_hf_text_completion_function):
    kernel, text2text_function, simple_input = setup_hf_text_completion_function

    # Complete input string and print
    summary = await kernel.run_async(text2text_function, input_str=simple_input)

    output = str(summary).strip()
    print(f"Completion using input string: '{output}'")
    assert len(output) > 0


@pytest.mark.asyncio
async def test_text2text_generation_input_vars(setup_hf_text_completion_function):
    kernel, text2text_function, simple_input = setup_hf_text_completion_function

    # Complete input as context variable and print
    context_vars = sk.ContextVariables(simple_input)
    summary = await kernel.run_async(text2text_function, input_vars=context_vars)

    output = str(summary).strip()
    print(f"Completion using context variables: '{output}'")
    assert len(output) > 0


@pytest.mark.asyncio
async def test_text2text_generation_input_context(setup_hf_text_completion_function):
    kernel, text2text_function, simple_input = setup_hf_text_completion_function

    # Complete input context and print
    context = kernel.create_new_context()
    context["input"] = simple_input
    summary = await kernel.run_async(text2text_function, input_context=context)

    output = str(summary).strip()
    print(f"Completion using input context: '{output}'")
    assert len(output) > 0


@pytest.mark.asyncio
async def test_text2text_generation_input_context_with_vars(
    setup_hf_text_completion_function,
):
    kernel, text2text_function, simple_input = setup_hf_text_completion_function

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
    setup_hf_text_completion_function,
):
    kernel, text2text_function, simple_input = setup_hf_text_completion_function

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
    setup_hf_text_completion_function,
):
    kernel, text2text_function, simple_input = setup_hf_text_completion_function

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


@pytest.mark.asyncio
async def test_text_generation_with_kwargs(
    setup_hf_text_completion_function,
):
    _, _, simple_input = setup_hf_text_completion_function
    
    model_name = "tiiuae/falcon-7b-instruct"
    
    tokenizer = AutoTokenizer.from_pretrained(
        pretrained_model_name_or_path=model_name,
        trust_remote_code=True)
    
    hf_model = sk_hf.HuggingFaceTextCompletion(
        model_name,
        task="text-generation",
        model_kwargs={
            "torch_dtype": torch.bfloat16
        },
        pipeline_kwargs={
            "tokenizer": tokenizer,
            "trust_remote_code": True
        }
    )
    
    kernel = sk.Kernel()
    
    # Configure LLM service
    kernel.add_text_completion_service(
        "falcon-7b",
        hf_model
    )
    
    # Define semantic function using SK prompt template language
    sk_prompt = "Hello, I like {{$input}}{{$input2}}"
    text2text_function = kernel.create_semantic_function(sk_prompt, max_tokens=25, temperature=0.2, top_p=0.5)

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
