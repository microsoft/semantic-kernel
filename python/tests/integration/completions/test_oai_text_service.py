# Copyright (c) Microsoft. All rights reserved.

import pytest
from openai import AsyncOpenAI
from test_utils import retry

import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.open_ai.settings.open_ai_settings import OpenAISettings
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


@pytest.mark.asyncio
async def test_oai_text_completion_with_plugins(setup_tldr_function_for_oai_models):
    kernel, prompt, text_to_summarize = setup_tldr_function_for_oai_models

    kernel.add_service(
        sk_oai.OpenAITextCompletion(service_id="text-completion", ai_model_id="gpt-3.5-turbo-instruct"),
    )

    exec_settings = PromptExecutionSettings(
        service_id="text-completion", extension_data={"max_tokens": 200, "temperature": 0, "top_p": 0.5}
    )

    prompt_template_config = PromptTemplateConfig(
        template=prompt, description="Write a short story.", execution_settings=exec_settings
    )

    # Create the semantic function
    tldr_function = kernel.add_function(
        function_name="story", plugin_name="plugin", prompt_template_config=prompt_template_config
    )

    arguments = KernelArguments(input=text_to_summarize)

    summary = await retry(lambda: kernel.invoke(tldr_function, arguments))
    output = str(summary).strip()
    print(f"TLDR using input string: '{output}'")
    # assert "First Law" not in output and ("human" in output or "Human" in output or "preserve" in output)
    assert 0 < len(output) < 100


@pytest.mark.asyncio
async def test_oai_text_completion_with_plugins_with_provided_client(setup_tldr_function_for_oai_models):
    kernel, prompt, text_to_summarize = setup_tldr_function_for_oai_models

    openai_settings = OpenAISettings.create()
    api_key = openai_settings.api_key.get_secret_value()
    org_id = openai_settings.org_id

    client = AsyncOpenAI(
        api_key=api_key,
        organization=org_id,
    )

    kernel.add_service(
        sk_oai.OpenAITextCompletion(
            service_id="text-completion",
            ai_model_id="gpt-3.5-turbo-instruct",
            async_client=client,
        ),
        overwrite=True,
    )

    exec_settings = PromptExecutionSettings(
        service_id="text-completion", extension_data={"max_tokens": 200, "temperature": 0, "top_p": 0.5}
    )

    prompt_template_config = PromptTemplateConfig(
        template=prompt, description="Write a short story.", execution_settings=exec_settings
    )

    # Create the semantic function
    tldr_function = kernel.add_function(
        function_name="story",
        plugin_name="plugin",
        prompt_template_config=prompt_template_config,
    )

    arguments = KernelArguments(input=text_to_summarize)

    summary = await retry(lambda: kernel.invoke(tldr_function, arguments))
    output = str(summary).strip()
    print(f"TLDR using input string: '{output}'")
    # assert "First Law" not in output and ("human" in output or "Human" in output or "preserve" in output)
    assert 0 < len(output) < 100


@pytest.mark.asyncio
async def test_azure_oai_text_stream_completion_with_plugins(setup_tldr_function_for_oai_models):
    kernel, prompt, text_to_summarize = setup_tldr_function_for_oai_models

    # Configure LLM service
    kernel.add_service(
        sk_oai.AzureTextCompletion(
            service_id="text_completion",
        ),
    )

    # Create the semantic function
    exec_settings = PromptExecutionSettings(
        service_id="text_completion", extension_data={"max_tokens": 200, "temperature": 0, "top_p": 0.5}
    )

    prompt_template_config = PromptTemplateConfig(
        template=prompt, description="Write a short story.", execution_settings=exec_settings
    )

    # Create the semantic function
    tldr_function = kernel.add_function(
        function_name="story",
        plugin_name="plugin",
        prompt_template_config=prompt_template_config,
    )

    arguments = KernelArguments(input=text_to_summarize)

    result = None
    async for message in kernel.invoke_stream(tldr_function, arguments):
        result = message[0] if not result else result + message[0]
    output = str(result)

    print(f"TLDR using input string: '{output}'")
    # assert "First Law" not in output and ("human" in output or "Human" in output or "preserve" in output)
    assert 0 < len(output) < 100
