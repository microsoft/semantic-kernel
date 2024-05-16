# Copyright (c) Microsoft. All rights reserved.


import pytest
from openai import AsyncAzureOpenAI

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.open_ai.settings.azure_open_ai_settings import AzureOpenAISettings
from semantic_kernel.core_plugins.text_memory_plugin import TextMemoryPlugin
from semantic_kernel.kernel import Kernel
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory
from semantic_kernel.memory.volatile_memory_store import VolatileMemoryStore


@pytest.mark.asyncio
async def test_azure_text_embedding_service(kernel: Kernel):
    embeddings_gen = sk_oai.AzureTextEmbedding(
        service_id="aoai-ada",
    )

    kernel.add_service(embeddings_gen)

    memory = SemanticTextMemory(storage=VolatileMemoryStore(), embeddings_generator=embeddings_gen)
    kernel.add_plugin(TextMemoryPlugin(memory), "TextMemoryPlugin")

    await memory.save_information(collection="generic", id="info1", text="My budget for 2024 is $100,000")
    await memory.save_reference(
        "test",
        external_id="info1",
        text="this is a test",
        external_source_name="external source",
    )


@pytest.mark.asyncio
async def test_azure_text_embedding_service_with_provided_client(kernel: Kernel):

    azure_openai_settings = AzureOpenAISettings.create()
    endpoint = azure_openai_settings.endpoint
    deployment_name = azure_openai_settings.embedding_deployment_name
    api_key = azure_openai_settings.api_key.get_secret_value()
    api_version = azure_openai_settings.api_version

    client = AsyncAzureOpenAI(
        azure_endpoint=endpoint,
        azure_deployment=deployment_name,
        api_key=api_key,
        api_version=api_version,
        default_headers={"Test-User-X-ID": "test"},
    )

    embeddings_gen = sk_oai.AzureTextEmbedding(
        service_id="aoai-ada-2",
        async_client=client,
    )

    kernel.add_service(embeddings_gen)
    memory = SemanticTextMemory(storage=sk.memory.VolatileMemoryStore(), embeddings_generator=embeddings_gen)
    kernel.add_plugin(TextMemoryPlugin(memory), "TextMemoryPlugin")

    await memory.save_information(collection="generic", id="info1", text="My budget for 2024 is $100,000")
    await memory.save_reference(
        "test",
        external_id="info1",
        text="this is a test",
        external_source_name="external source",
    )


@pytest.mark.asyncio
async def test_batch_azure_embeddings():
    # Configure LLM service
    embeddings_service = sk_oai.AzureTextEmbedding(service_id="aoai-ada")
    texts = ["hello world"]
    results = await embeddings_service.generate_embeddings(texts)
    batch_results = await embeddings_service.generate_embeddings(texts, batch_size=1)
    assert len(results) == len(batch_results)
