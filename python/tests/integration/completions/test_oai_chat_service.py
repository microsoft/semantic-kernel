# Copyright (c) Microsoft. All rights reserved.
import os

import pytest
from openai import AsyncOpenAI
from test_utils import retry

import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


@pytest.mark.asyncio
async def test_oai_chat_service_with_plugins(setup_tldr_function_for_oai_models, get_oai_config):
    kernel, prompt, text_to_summarize = setup_tldr_function_for_oai_models

    api_key, org_id = get_oai_config

    print("* Service: OpenAI Chat Completion")
    print("* Endpoint: OpenAI")
    print("* Model: gpt-3.5-turbo")

    kernel.add_service(
        sk_oai.OpenAIChatCompletion(service_id="chat-gpt", ai_model_id="gpt-3.5-turbo", api_key=api_key, org_id=org_id),
    )

    exec_settings = PromptExecutionSettings(
        service_id="chat-gpt", extension_data={"max_tokens": 200, "temperature": 0, "top_p": 0.5}
    )

    prompt_template_config = PromptTemplateConfig(
        template=prompt, description="Write a short story.", execution_settings=exec_settings
    )

    # Create the semantic function
    tldr_function = kernel.create_function_from_prompt(
        function_name="story", plugin_name="plugin", prompt_template_config=prompt_template_config
    )

    summary = await retry(lambda: kernel.invoke(tldr_function, input=text_to_summarize))
    output = str(summary).strip()
    print(f"TLDR using input string: '{output}'")
    assert "First Law" not in output and ("human" in output or "Human" in output or "preserve" in output)
    assert len(output) < 100


@pytest.mark.asyncio
async def test_oai_chat_service_with_plugins_with_provided_client(setup_tldr_function_for_oai_models, get_oai_config):
    kernel, prompt, text_to_summarize = setup_tldr_function_for_oai_models

    api_key, org_id = get_oai_config

    print("* Service: OpenAI Chat Completion")
    print("* Endpoint: OpenAI")
    print("* Model: gpt-3.5-turbo")

    client = AsyncOpenAI(
        api_key=api_key,
        organization=org_id,
    )

    kernel.add_service(
        sk_oai.OpenAIChatCompletion(
            service_id="chat-gpt",
            ai_model_id="gpt-3.5-turbo",
            async_client=client,
        ),
        overwrite=True,  # Overwrite the service if it already exists since add service says it does
    )

    exec_settings = PromptExecutionSettings(
        service_id="chat-gpt", extension_data={"max_tokens": 200, "temperature": 0, "top_p": 0.5}
    )

    prompt_template_config = PromptTemplateConfig(
        template=prompt, description="Write a short story.", execution_settings=exec_settings
    )

    # Create the semantic function
    tldr_function = kernel.create_function_from_prompt(
        function_name="story",
        plugin_name="story_plugin",
        prompt_template_config=prompt_template_config,
    )

    summary = await retry(lambda: kernel.invoke(tldr_function, input=text_to_summarize))
    output = str(summary).strip()
    print(f"TLDR using input string: '{output}'")
    assert "First Law" not in output and ("human" in output or "Human" in output or "preserve" in output)
    assert len(output) < 100


@pytest.mark.asyncio
async def test_oai_chat_stream_service_with_plugins(setup_tldr_function_for_oai_models, get_aoai_config):
    kernel, prompt, text_to_summarize = setup_tldr_function_for_oai_models

    _, api_key, endpoint = get_aoai_config

    if "Python_Integration_Tests" in os.environ:
        deployment_name = os.environ["AzureOpenAIChat__DeploymentName"]
    else:
        deployment_name = "gpt-35-turbo"

    print("* Service: Azure OpenAI Chat Completion")
    print(f"* Endpoint: {endpoint}")
    print(f"* Deployment: {deployment_name}")

    # Configure LLM service
    kernel.add_service(
        sk_oai.AzureChatCompletion(
            service_id="chat_completion", deployment_name=deployment_name, endpoint=endpoint, api_key=api_key
        ),
        overwrite=True,
    )

    exec_settings = PromptExecutionSettings(
        service_id="chat_completion", extension_data={"max_tokens": 200, "temperature": 0, "top_p": 0.5}
    )

    prompt_template_config = PromptTemplateConfig(
        template=prompt, description="Write a short story.", execution_settings=exec_settings
    )

    # Create the prompt function
    tldr_function = kernel.create_function_from_prompt(
        function_name="story",
        plugin_name="story_plugin",
        prompt_template_config=prompt_template_config,
    )

    result = None
    async for message in kernel.invoke_stream(tldr_function, input=text_to_summarize):
        result = message[0] if not result else result + message[0]
    output = str(result)

    print(f"TLDR using input string: '{output}'")
    # assert "First Law" not in output and ("human" in output or "Human" in output or "preserve" in output)
    assert 0 < len(output) < 100
