# Copyright (c) Microsoft. All rights reserved.


import pytest
from openai import AsyncAzureOpenAI
from test_utils import retry

import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.open_ai.settings.azure_open_ai_settings import AzureOpenAISettings
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig


@pytest.mark.asyncio
async def test_azure_e2e_text_completion_with_plugin(setup_tldr_function_for_oai_models):
    kernel, prompt, text_to_summarize = setup_tldr_function_for_oai_models

    service_id = "text_completion"

    # Configure LLM service
    kernel.add_service(
        sk_oai.AzureTextCompletion(
            service_id=service_id,
        ),
    )

    exec_settings = PromptExecutionSettings(
        service_id=service_id, extension_data={"max_tokens": 200, "temperature": 0, "top_p": 0.5}
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
    assert len(output) < 100


@pytest.mark.asyncio
async def test_azure_e2e_text_completion_with_plugin_with_provided_client(setup_tldr_function_for_oai_models):
    kernel, prompt, text_to_summarize = setup_tldr_function_for_oai_models

    azure_openai_settings = AzureOpenAISettings.create()
    endpoint = azure_openai_settings.endpoint
    deployment_name = azure_openai_settings.text_deployment_name
    api_key = azure_openai_settings.api_key.get_secret_value()
    api_version = azure_openai_settings.api_version

    client = AsyncAzureOpenAI(
        azure_endpoint=endpoint,
        azure_deployment=deployment_name,
        api_key=api_key,
        api_version=api_version,
        default_headers={"Test-User-X-ID": "test"},
    )

    service_id = "text_completion"

    # Configure LLM service
    kernel.add_service(
        sk_oai.AzureTextCompletion(
            service_id=service_id,
            async_client=client,
        ),
        overwrite=True,  # Overwrite the service for the test if it already exists
    )

    exec_settings = PromptExecutionSettings(
        service_id=service_id, extension_data={"max_tokens": 200, "temperature": 0, "top_p": 0.5}
    )

    prompt_template_config = PromptTemplateConfig(
        template=prompt, description="Write a short story.", execution_settings=exec_settings
    )

    # Create the semantic function
    tldr_function = kernel.add_function(
        function_name="tldr", plugin_name="plugin", prompt_template_config=prompt_template_config
    )

    arguments = KernelArguments(input=text_to_summarize)

    summary = await retry(lambda: kernel.invoke(tldr_function, arguments))
    output = str(summary).strip()
    print(f"TLDR using input string: '{output}'")
    assert len(output) > 0
