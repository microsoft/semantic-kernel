# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

import e2e_memories
import pytest

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai


@pytest.mark.asyncio
# @pytest.mark.xfail(raises=AssertionError, reason="OpenAI may throttle requests, preventing this test from passing")
async def test_oai_embedding_service_with_memories():
    kernel = sk.Kernel()

    if "Python_Integration_Tests" in os.environ:
        api_key = os.environ["OpenAI__ApiKey"]
        org_id = None
    else:
        # Load credentials from .env file
        api_key, org_id = sk.openai_settings_from_dot_env()

    kernel.add_text_embedding_generation_service(
        "oai-ada", sk_oai.OpenAITextEmbedding("text-embedding-ada-002", api_key, org_id)
    )
    kernel.register_memory_store(memory_store=sk.memory.VolatileMemoryStore())

    await e2e_memories.simple_memory_test(kernel)


if __name__ == "__main__":
    asyncio.run(test_oai_embedding_service_with_memories())
