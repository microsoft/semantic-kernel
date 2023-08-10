# Copyright (c) Microsoft. All rights reserved.
import pytest
import semantic_kernel as sk
import semantic_kernel.connectors.ai.jina_ai as sk_jai

@pytest.mark.asyncio
async def test_jina_embedding_service(create_kernel, get_jai_config):
    kernel = create_kernel
    api_key, model_id, org_id = get_jai_config

    kernel.add_text_embedding_generation_service(
        model_id,
        sk_jai.JinaTextEmbedding(model_id=model_id, api_key=api_key, org_id=org_id),
    )
    kernel.register_memory_store(memory_store=sk.memory.VolatileMemoryStore())

    # Add some documents to the semantic memory
    await kernel.memory.save_information_async(
        "test", id="info1", text="this is a test"
    )
    await kernel.memory.save_reference_async(
        "test",
        external_id="info1",
        text="this is a test",
        external_source_name="external source",
    )