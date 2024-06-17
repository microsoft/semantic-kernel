# Copyright (c) Microsoft. All rights reserved.

import pytest

import semantic_kernel.connectors.ai.azure_ai_inference as sk_aai
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
from tests.integration.completions.test_utils import retry


@pytest.mark.asyncio
async def test_azure_ai_inference_chat_service(setup_tldr_function_for_oai_models):
    """Test Azure AI Inference Chat Service."""
    kernel, prompt, text_to_summarize = setup_tldr_function_for_oai_models

    azure_ai_inference_chat_service = sk_aai.AzureAIInferenceChatCompletion()
    kernel.add_service(azure_ai_inference_chat_service)

    print("* Service: Azure AI Inference Chat Completion")
    print(f"* Model: ${azure_ai_inference_chat_service.ai_model_id}")

    # Create the semantic function
    exec_settings = sk_aai.AzureAIInferenceChatPromptExecutionSettings(
        max_tokens=200,
        temperature=0,
        top_p=0.5,
    )

    prompt_template_config = PromptTemplateConfig(
        template=prompt,
        execution_settings=exec_settings,
    )

    # Create the semantic function
    tldr_function = kernel.add_function(
        function_name="tldr",
        plugin_name="plugin",
        prompt_template_config=prompt_template_config,
    )

    arguments = KernelArguments(input=text_to_summarize)
    summary = await retry(lambda: kernel.invoke(tldr_function, arguments))
    output = str(summary).strip()
    print(f"Function {tldr_function.name} output: '{output}'")
    assert len(output) > 0
