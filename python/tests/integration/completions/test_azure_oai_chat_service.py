# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

import e2e_text_completion
import pytest

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai


@pytest.mark.asyncio
@pytest.mark.xfail(
    raises=AssertionError,
    reason="Azure OpenAI may throttle requests, preventing this test from passing",
)
async def test_azure_chat_completion_with_skills():
    kernel = sk.Kernel()

    if "Python_Integration_Tests" in os.environ:
        deployment_name = os.environ["AzureOpenAIChat__DeploymentName"]
        api_key = os.environ["AzureOpenAI__ApiKey"]
        endpoint = os.environ["AzureOpenAI__Endpoint"]
    else:
        # Load credentials from .env file
        deployment_name, api_key, endpoint = sk.azure_openai_settings_from_dot_env()
        deployment_name = "gpt-4"

    # Configure LLM service
    kernel.add_chat_service(
        "chat_completion",
        sk_oai.AzureChatCompletion(deployment_name, endpoint, api_key),
    )

    await e2e_text_completion.summarize_function_test(kernel)


if __name__ == "__main__":
    asyncio.run(test_azure_chat_completion_with_skills())
