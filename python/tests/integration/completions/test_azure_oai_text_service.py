# Copyright (c) Microsoft. All rights reserved.

import os

import pytest
from test_utils import retry

import semantic_kernel.connectors.ai.open_ai as sk_oai


def get_aoai_api_versions():
    api_versiosn = os.environ["AzureOpenAI__APIVersions"]
    return api_versiosn.split(",")


@pytest.mark.asyncio
@pytest.mark.parametrize("api_version", get_aoai_api_versions())
async def test_azure_e2e_text_completion_with_skill(
    setup_tldr_function_for_oai_models, get_aoai_config, api_version
):
    kernel, sk_prompt, text_to_summarize = setup_tldr_function_for_oai_models

    _, api_key, endpoint = get_aoai_config

    if "Python_Integration_Tests" in os.environ:
        deployment_name = os.environ["AzureOpenAI__DeploymentName"]
    else:
        deployment_name = "text-davinci-003"

    print("* Service: Azure OpenAI Text Completion")
    print(f"* Endpoint: {endpoint}")
    print(f"* Deployment: {deployment_name}")

    # Configure LLM service
    kernel.add_text_completion_service(
        "text_completion",
        sk_oai.AzureTextCompletion(deployment_name, endpoint, api_key, api_version),
    )

    # Create the semantic function
    tldr_function = kernel.create_semantic_function(
        sk_prompt, max_tokens=200, temperature=0, top_p=0.5
    )

    summary = await retry(
        lambda: kernel.run_async(tldr_function, input_str=text_to_summarize)
    )
    output = str(summary).strip()
    print(f"TLDR using input string: '{output}'")
    assert "First Law" not in output and (
        any(word in output for word in ["human", "Human", "preserve", "harm"])
    )
    assert len(output) < 100


@pytest.mark.asyncio
@pytest.mark.parametrize("api_version", get_aoai_api_versions())
async def test_oai_text_stream_completion_with_skills(
    setup_tldr_function_for_oai_models, get_aoai_config, api_version
):
    kernel, sk_prompt, text_to_summarize = setup_tldr_function_for_oai_models

    _, api_key, endpoint = get_aoai_config

    if "Python_Integration_Tests" in os.environ:
        deployment_name = os.environ["AzureOpenAI__DeploymentName"]
    else:
        deployment_name = "text-davinci-003"

    print("* Service: Azure OpenAI Text Completion")
    print(f"* Endpoint: {endpoint}")
    print(f"* Deployment: {deployment_name}")

    # Configure LLM service
    kernel.add_text_completion_service(
        "text_completion",
        sk_oai.AzureTextCompletion(deployment_name, endpoint, api_key, api_version),
    )

    # Create the semantic function
    tldr_function = kernel.create_semantic_function(
        sk_prompt, max_tokens=200, temperature=0, top_p=0.5
    )

    result = []
    async for message in kernel.run_stream_async(
        tldr_function, input_str=text_to_summarize
    ):
        result.append(message)
    output = "".join(result).strip()

    print(f"TLDR using input string: '{output}'")
    assert len(result) > 1
    assert "First Law" not in output and (
        any(word in output for word in ["human", "Human", "preserve", "harm"])
    )
    assert len(output) < 100
