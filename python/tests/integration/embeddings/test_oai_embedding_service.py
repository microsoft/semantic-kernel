# Copyright (c) Microsoft. All rights reserved.

import pytest
from openai import AsyncOpenAI

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.kernel import Kernel
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory


@pytest.mark.asyncio
async def test_oai_embedding_service(kernel: Kernel, get_oai_config):
    api_key, org_id = get_oai_config

    embedding_gen = sk_oai.OpenAITextEmbedding(
        service_id="oai-ada", ai_model_id="text-embedding-ada-002", api_key=api_key, org_id=org_id
    )

    kernel.add_service(embedding_gen)

    memory = SemanticTextMemory(storage=sk.memory.VolatileMemoryStore(), embeddings_generator=embedding_gen)
    kernel.import_plugin_from_object(sk.core_plugins.TextMemoryPlugin(memory), "TextMemoryPlugin")

    await memory.save_reference(
        "test",
        external_id="info1",
        text="this is a test",
        external_source_name="external source",
    )


@pytest.mark.asyncio
async def test_oai_embedding_service_with_provided_client(kernel: Kernel, get_oai_config):
    api_key, org_id = get_oai_config

    client = AsyncOpenAI(
        api_key=api_key,
        organization=org_id,
    )

    embedding_gen = sk_oai.OpenAITextEmbedding(
        service_id="oai-ada", ai_model_id="text-embedding-ada-002", async_client=client
    )

    kernel.add_service(embedding_gen)
    memory = SemanticTextMemory(storage=sk.memory.VolatileMemoryStore(), embeddings_generator=embedding_gen)
    kernel.import_plugin_from_object(sk.core_plugins.TextMemoryPlugin(memory), "TextMemoryPlugin")

    await memory.save_reference(
        "test",
        external_id="info1",
        text="this is a test",
        external_source_name="external source",
    )
