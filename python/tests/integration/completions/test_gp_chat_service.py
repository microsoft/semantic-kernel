# Copyright (c) Microsoft. All rights reserved.

import os
import sys

import pytest
from test_utils import retry

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

if sys.version_info >= (3, 9):
    import semantic_kernel.connectors.ai.google_palm as sk_gp

pytestmark = [
    pytest.mark.skipif(sys.version_info < (3, 9), reason="Google Palm requires Python 3.9 or greater"),
    pytest.mark.skipif(
        "Python_Integration_Tests" in os.environ,
        reason="Google Palm integration tests are only set up to run locally",
    ),
]


@pytest.mark.asyncio
async def test_gp_chat_service_with_plugins(setup_tldr_function_for_oai_models, get_gp_config):
    kernel, prompt, text_to_summarize = setup_tldr_function_for_oai_models
    api_key = get_gp_config

    print("* Service: Google PaLM Chat Completion")
    print("* Model: chat-bison-001")
    model_id = "models/chat-bison-001"
    palm_chat_completion = sk_gp.GooglePalmChatCompletion(ai_model_id=model_id, api_key=api_key)
    kernel.add_service(palm_chat_completion)

    exec_settings = PromptExecutionSettings(
        service_id=model_id, extension_data={"max_tokens": 200, "temperature": 0, "top_p": 0.5}
    )

    prompt_template_config = PromptTemplateConfig(template=prompt, execution_settings=exec_settings)

    # Create the semantic function
    tldr_function = kernel.create_function_from_prompt(prompt_template_config=prompt_template_config)

    arguments = KernelArguments(input=text_to_summarize)

    summary = await retry(lambda: kernel.invoke(tldr_function, arguments))
    output = str(summary).strip()
    print(f"TLDR using input string: '{output}'")
    # assert "First Law" not in output and ("human" in output or "Human" in output or "preserve" in output)
    assert len(output) > 0
