# Copyright (c) Microsoft. All rights reserved.

import os

import pytest
from openai import AsyncAzureOpenAI
from test_utils import retry

import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.open_ai.utils import get_tool_call_object
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.core_plugins.math_plugin import MathPlugin
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


@pytest.mark.asyncio
async def test_azure_e2e_chat_completion_with_plugin(setup_tldr_function_for_oai_models, get_aoai_config):
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
            service_id="chat", deployment_name=deployment_name, endpoint=endpoint, api_key=api_key
        ),
    )

    exec_settings = PromptExecutionSettings(
        service_id="chat", extension_data={"max_tokens": 200, "temperature": 0, "top_p": 0.5}
    )

    prompt_template_config = PromptTemplateConfig(
        template=prompt, description="Write a short story.", execution_settings=exec_settings
    )

    # Create the semantic function
    tldr_function = kernel.create_function_from_prompt(
        function_name="tldr", plugin_name="plugin", prompt_template_config=prompt_template_config
    )

    arguments = KernelArguments(input=text_to_summarize)

    summary = await retry(lambda: kernel.invoke(tldr_function, arguments))
    output = str(summary).strip()
    print(f"TLDR using input string: '{output}'")
    assert "First Law" not in output and ("human" in output or "Human" in output or "preserve" in output)
    assert len(output) < 100


@pytest.mark.asyncio
async def test_azure_e2e_chat_completion_with_plugin_and_provided_client(
    setup_tldr_function_for_oai_models, get_aoai_config
):
    kernel, prompt, text_to_summarize = setup_tldr_function_for_oai_models

    _, api_key, endpoint = get_aoai_config

    if "Python_Integration_Tests" in os.environ:
        deployment_name = os.environ["AzureOpenAIChat__DeploymentName"]
    else:
        deployment_name = "gpt-35-turbo"

    print("* Service: Azure OpenAI Chat Completion")
    print(f"* Endpoint: {endpoint}")
    print(f"* Deployment: {deployment_name}")

    client = AsyncAzureOpenAI(
        azure_endpoint=endpoint,
        azure_deployment=deployment_name,
        api_key=api_key,
        api_version="2024-02-01",
        default_headers={"Test-User-X-ID": "test"},
    )

    # Configure LLM service
    kernel.add_service(
        sk_oai.AzureChatCompletion(
            service_id="chat_completion",
            deployment_name=deployment_name,
            async_client=client,
        ),
    )

    exec_settings = PromptExecutionSettings(
        service_id="chat_completion", extension_data={"max_tokens": 200, "temperature": 0, "top_p": 0.5}
    )

    prompt_template_config = PromptTemplateConfig(
        template=prompt, description="Write a short story.", execution_settings=exec_settings
    )

    # Create the semantic function
    tldr_function = kernel.create_function_from_prompt(
        function_name="tldr", plugin_name="plugin", prompt_template_config=prompt_template_config
    )

    arguments = KernelArguments(input=text_to_summarize)

    summary = await retry(lambda: kernel.invoke(tldr_function, arguments))
    output = str(summary).strip()
    print(f"TLDR using input string: '{output}'")
    assert "First Law" not in output and ("human" in output or "Human" in output or "preserve" in output)
    assert len(output) < 100


@pytest.mark.asyncio
async def test_azure_oai_chat_service_with_tool_call(setup_tldr_function_for_oai_models, get_aoai_config):
    kernel, _, _ = setup_tldr_function_for_oai_models

    _, api_key, endpoint = get_aoai_config

    if "Python_Integration_Tests" in os.environ:
        deployment_name = os.environ["AzureOpenAIChat__DeploymentName"]
    else:
        deployment_name = "gpt-35-turbo"

    print("* Service: Azure OpenAI Chat Completion")
    print(f"* Endpoint: {endpoint}")
    print(f"* Deployment: {deployment_name}")

    client = AsyncAzureOpenAI(
        azure_endpoint=endpoint,
        azure_deployment=deployment_name,
        api_key=api_key,
        api_version="2024-02-01",
        default_headers={"Test-User-X-ID": "test"},
    )

    # Configure LLM service
    kernel.add_service(
        sk_oai.AzureChatCompletion(
            service_id="chat_completion",
            deployment_name=deployment_name,
            async_client=client,
        ),
    )

    kernel.import_plugin_from_object(MathPlugin(), plugin_name="math")

    execution_settings = sk_oai.AzureChatPromptExecutionSettings(
        service_id="chat_completion",
        max_tokens=2000,
        temperature=0.7,
        top_p=0.8,
        tool_choice="auto",
        tools=get_tool_call_object(kernel, {"exclude_plugin": ["ChatBot"]}),
        auto_invoke_kernel_functions=True,
        max_auto_invoke_attempts=3,
    )

    prompt_template_config = PromptTemplateConfig(
        template="{{$input}}", description="Do math.", execution_settings=execution_settings
    )

    # Create the prompt function
    tldr_function = kernel.create_function_from_prompt(
        function_name="math_fun", plugin_name="math_int_test", prompt_template_config=prompt_template_config
    )

    summary = await retry(lambda: kernel.invoke(tldr_function, input="what is 1+1?"))
    output = str(summary).strip()
    print(f"Math output: '{output}'")
    assert "2" in output
    assert 0 < len(output) < 100


@pytest.mark.asyncio
async def test_azure_oai_chat_service_with_tool_call_streaming(kernel: Kernel, get_aoai_config):
    _, api_key, endpoint = get_aoai_config

    if "Python_Integration_Tests" in os.environ:
        deployment_name = os.environ["AzureOpenAIChat__DeploymentName"]
    else:
        deployment_name = "gpt-35-turbo"

    print("* Service: Azure OpenAI Chat Completion")
    print(f"* Endpoint: {endpoint}")
    print(f"* Deployment: {deployment_name}")

    client = AsyncAzureOpenAI(
        azure_endpoint=endpoint,
        azure_deployment=deployment_name,
        api_key=api_key,
        api_version="2024-02-01",
        default_headers={"Test-User-X-ID": "test"},
    )

    # Configure LLM service
    kernel.add_service(
        sk_oai.AzureChatCompletion(
            service_id="chat_completion",
            deployment_name=deployment_name,
            async_client=client,
        ),
    )

    kernel.import_plugin_from_object(MathPlugin(), plugin_name="Math")

    # Create the prompt function
    chat_func = kernel.create_function_from_prompt(prompt="{{$input}}", function_name="chat", plugin_name="chat")
    execution_settings = sk_oai.AzureChatPromptExecutionSettings(
        service_id="chat_completion",
        max_tokens=2000,
        temperature=0.7,
        top_p=0.8,
        tool_choice="auto",
        tools=get_tool_call_object(kernel, {"exclude_plugin": ["chat"]}),
        auto_invoke_kernel_functions=True,
        max_auto_invoke_attempts=3,
    )
    arguments = KernelArguments(input="what is 101+102?", settings=execution_settings)

    result = None
    async for message in kernel.invoke_stream(chat_func, arguments=arguments):
        result = message[0] if not result else result + message[0]
    output = str(result)

    print(f"Math output: '{output}'")
    assert "2" in output
    assert 0 < len(output) < 100
