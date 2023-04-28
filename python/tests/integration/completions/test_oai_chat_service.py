# Copyright (c) Microsoft. All rights reserved.

import os
import pytest
import sys
import asyncio
import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
import e2e_text_completion

@pytest.mark.asyncio
@pytest.mark.xfail(raises=AssertionError, reason="OpenAI may throtle requests, preventing this test from passing")
async def test_oai_chat_service_with_skills(use_env_vars: bool):
    kernel = sk.Kernel()

    if use_env_vars:
        api_key = os.environ["OpenAI__ApiKey"]
        org_id = None
    else:
        # Load credentials from .env file
        api_key, org_id = sk.openai_settings_from_dot_env()

    kernel.config.add_chat_service(
        "chat-gpt", sk_oai.OpenAIChatCompletion("gpt-3.5-turbo", api_key, org_id)
    )

    await e2e_text_completion.summarize_function_test(kernel)

if __name__ == "__main__":
    asyncio.run(test_oai_chat_service_with_skills("--use-env-vars" in sys.argv))