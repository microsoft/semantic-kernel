# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

import e2e_memories
import pytest

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai


@pytest.mark.asyncio
async def test_azure_text_embeddings_with_memories():
    kernel = sk.Kernel()

    if "Python_Integration_Tests" in os.environ:
        deployment_name = os.environ["AzureOpenAIEmbeddings__DeploymentName"]
        api_key = os.environ["AzureOpenAI__ApiKey"]
        endpoint = os.environ["AzureOpenAI__Endpoint"]
    else:
        # Load credentials from .env file
        deployment_name, api_key, endpoint = sk.azure_openai_settings_from_dot_env()
        deployment_name = "text-embedding-ada-002"

    kernel.add_text_embedding_generation_service(
        "aoai-ada", sk_oai.AzureTextEmbedding(deployment_name, endpoint, api_key)
    )
    kernel.register_memory_store(memory_store=sk.memory.VolatileMemoryStore())

    await e2e_memories.simple_memory_test(kernel)


if __name__ == "__main__":
    asyncio.run(test_azure_text_embeddings_with_memories())
