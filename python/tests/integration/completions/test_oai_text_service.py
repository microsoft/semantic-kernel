# Copyright (c) Microsoft. All rights reserved.
import os

import pytest
from openai import AsyncOpenAI
from test_utils import retry

import semantic_kernel.connectors.ai.open_ai as sk_oai


@pytest.mark.asyncio
async def test_oai_text_completion_with_plugins(setup_tldr_function_for_oai_models, get_oai_config):
    kernel, sk_prompt, text_to_summarize = setup_tldr_function_for_oai_models

    api_key, org_id = get_oai_config

    print("* Service: OpenAI Text Completion")
    print("* Endpoint: OpenAI")
    print("* Model: gpt-3.5-turbo-instruct")

    kernel.add_text_completion_service(
        "text-completion",
        sk_oai.OpenAITextCompletion(ai_model_id="gpt-3.5-turbo-instruct", api_key=api_key, org_id=org_id),
    )

    # Create the semantic function
    tldr_function = kernel.create_semantic_function(sk_prompt, max_tokens=200, temperature=0, top_p=0.5)

    summary = await retry(lambda: kernel.run(tldr_function, input_str=text_to_summarize))
    output = str(summary).strip()
    print(f"TLDR using input string: '{output}'")
    # assert "First Law" not in output and ("human" in output or "Human" in output or "preserve" in output)
    assert 0 < len(output) < 100


@pytest.mark.asyncio
async def test_oai_text_completion_with_plugins_with_provided_client(
    setup_tldr_function_for_oai_models, get_oai_config
):
    kernel, sk_prompt, text_to_summarize = setup_tldr_function_for_oai_models

    api_key, org_id = get_oai_config

    print("* Service: OpenAI Text Completion")
    print("* Endpoint: OpenAI")
    print("* Model: gpt-3.5-turbo-instruct")

    client = AsyncOpenAI(
        api_key=api_key,
        organization=org_id,
    )

    kernel.add_text_completion_service(
        "text-completion",
        sk_oai.OpenAITextCompletion(
            ai_model_id="gpt-3.5-turbo-instruct",
            async_client=client,
        ),
    )

    # Create the semantic function
    tldr_function = kernel.create_semantic_function(sk_prompt, max_tokens=200, temperature=0, top_p=0.5)

    summary = await retry(lambda: kernel.run(tldr_function, input_str=text_to_summarize))
    output = str(summary).strip()
    print(f"TLDR using input string: '{output}'")
    # assert "First Law" not in output and ("human" in output or "Human" in output or "preserve" in output)
    assert 0 < len(output) < 100


@pytest.mark.asyncio
async def test_oai_text_stream_completion_with_plugins(setup_tldr_function_for_oai_models, get_aoai_config):
    kernel, sk_prompt, text_to_summarize = setup_tldr_function_for_oai_models

    _, api_key, endpoint = get_aoai_config

    if "Python_Integration_Tests" in os.environ:
        deployment_name = os.environ["AzureOpenAI__DeploymentName"]
    else:
        deployment_name = "gpt-3.5-turbo-instruct"

    print("* Service: Azure OpenAI Text Completion")
    print(f"* Endpoint: {endpoint}")
    print(f"* Deployment: {deployment_name}")

    # Configure LLM service
    kernel.add_text_completion_service(
        "text_completion",
        sk_oai.AzureTextCompletion(
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key=api_key,
        ),
    )

    # Create the semantic function
    tldr_function = kernel.create_semantic_function(sk_prompt, max_tokens=200, temperature=0, top_p=0.5)

    result = None
    async for message in kernel.run_stream(tldr_function, input_str=text_to_summarize):
        result = message[0] if not result else result + message[0]
    output = str(result)

    print(f"TLDR using input string: '{output}'")
    # assert "First Law" not in output and ("human" in output or "Human" in output or "preserve" in output)
    assert 0 < len(output) < 100
