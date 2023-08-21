# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
import sys

import pytest

import semantic_kernel.connectors.ai.google_palm as sk_gp

pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 9), reason="Google Palm requires Python 3.9 or greater"
)

pytestmark = pytest.mark.skipif(
    "Python_Integration_Tests" in os.environ,
    reason="Google Palm integration tests are only set up to run locally",
)


@pytest.mark.asyncio
async def test_gp_chat_service_with_skills(
    setup_tldr_function_for_oai_models, get_gp_config
):
    kernel, sk_prompt, text_to_summarize = setup_tldr_function_for_oai_models
    api_key = get_gp_config

    print("* Service: Google PaLM Chat Completion")
    print("* Model: chat-bison-001")
    palm_chat_completion = sk_gp.GooglePalmChatCompletion(
        "models/chat-bison-001", api_key
    )
    kernel.add_chat_service("models/chat-bison-001", palm_chat_completion)

    # Create the semantic function
    tldr_function = kernel.create_semantic_function(
        sk_prompt, max_tokens=200, temperature=0, top_p=0.5
    )

    max_retries = 5  # Adjust the number of retries as per your requirement
    retry_delay = 2  # Adjust the delay (in seconds) between retries

    for _ in range(max_retries):
        try:
            summary = await kernel.run_async(tldr_function, input_str=text_to_summarize)
            output = str(summary).strip()
            print(f"TLDR using input string: '{output}'")
            assert "First Law" not in output and (
                "human" in output or "Human" in output or "preserve" in output
            )
            assert len(output) < 100
            break
        except Exception as e:
            print(f"Error occurred: {e}")
            await asyncio.sleep(retry_delay)  # Introduce a delay before the next retry
    else:
        # The loop completed without breaking, meaning all retries failed
        raise AssertionError("Test failed after multiple retries")
