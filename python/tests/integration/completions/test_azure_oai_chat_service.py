# Copyright (c) Microsoft. All rights reserved.

import os

import pytest
from test_utils import retry

import semantic_kernel.connectors.ai.open_ai as sk_oai


@pytest.mark.asyncio
async def test_azure_e2e_chat_completion_with_skill(
    setup_tldr_function_for_oai_models, get_aoai_config
):
    kernel, sk_prompt, text_to_summarize = setup_tldr_function_for_oai_models

    _, api_key, endpoint = get_aoai_config

    if "Python_Integration_Tests" in os.environ:
        deployment_name = os.environ["AzureOpenAIChat__DeploymentName"]
    else:
        deployment_name = "gpt-35-turbo"

    print("* Service: Azure OpenAI Chat Completion")
    print(f"* Endpoint: {endpoint}")
    print(f"* Deployment: {deployment_name}")

    # Configure LLM service
    kernel.add_chat_service(
        "chat_completion",
        sk_oai.AzureChatCompletion(deployment_name, endpoint, api_key),
    )

    # Create the semantic function
    tldr_function = kernel.create_semantic_function(
        sk_prompt, max_tokens=200, temperature=0, top_p=0.5
    )

    output = await retry(
        lambda: kernel.run_async(tldr_function, input_str=text_to_summarize)
    )
    print(f"TLDR using input string: '{output}'")
    assert "First Law" not in output and (
        "human" in output or "Human" in output or "preserve" in output
    )
    assert len(output) < 100


@pytest.mark.asyncio
async def test_oai_chat_stream_service_with_skills(
    setup_tldr_function_for_oai_models, get_aoai_config
):
    kernel, sk_prompt, text_to_summarize = setup_tldr_function_for_oai_models

    _, api_key, endpoint = get_aoai_config

    if "Python_Integration_Tests" in os.environ:
        deployment_name = os.environ["AzureOpenAIChat__DeploymentName"]
    else:
        deployment_name = "gpt-35-turbo"

    print("* Service: Azure OpenAI Chat Completion")
    print(f"* Endpoint: {endpoint}")
    print(f"* Deployment: {deployment_name}")

    # Configure LLM service
    kernel.add_chat_service(
        "chat_completion",
        sk_oai.AzureChatCompletion(deployment_name, endpoint, api_key),
    )

    # Create the semantic function
    tldr_function = kernel.create_semantic_function(
        sk_prompt, max_tokens=200, temperature=0, top_p=0.5
    )

    result = []
    async for message in kernel.run_stream_async(
        tldr_function, input_str=text_to_summarize
    ):
        if message.choices[0].delta.content:
            result.append(message.choices[0].delta.content)
    output = "".join(result).strip()
    print(f"TLDR using input string: '{output}'")
    assert len(result) > 1
    assert "First Law" not in output and (
        "human" in output or "Human" in output or "preserve" in output
    )
    assert len(output) < 100
