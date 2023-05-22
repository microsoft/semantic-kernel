# Copyright (c) Microsoft. All rights reserved.

import pytest

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai


@pytest.mark.asyncio
async def test_oai_embedding_service(create_kernel, get_oai_config):
    kernel = create_kernel

    api_key, org_id = get_oai_config

    kernel.add_text_embedding_generation_service(
        "oai-ada",
        sk_oai.OpenAITextEmbedding("text-embedding-ada-002", api_key, org_id=org_id),
    )
    kernel.register_memory_store(memory_store=sk.memory.VolatileMemoryStore())

    await kernel.memory.save_information_async(
        "test", id="info1", text="this is a test"
    )
    await kernel.memory.save_reference_async(
        "test",
        external_id="info1",
        text="this is a test",
        external_source_name="external source",
    )
