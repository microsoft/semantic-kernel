# Copyright (c) Microsoft. All rights reserved.

import asyncio

import e2e_memories
import pytest

import semantic_kernel as sk
import semantic_kernel.connectors.ai.hugging_face as sk_hf


@pytest.mark.asyncio
async def test_hf_embeddings_with_memories():
    kernel = sk.Kernel()

    # Configure LLM service
    kernel.add_text_embedding_generation_service(
        "sentence-transformers/all-MiniLM-L6-v2",
        sk_hf.HuggingFaceTextEmbedding("sentence-transformers/all-MiniLM-L6-v2"),
    )
    kernel.register_memory_store(memory_store=sk.memory.VolatileMemoryStore())

    await e2e_memories.simple_memory_test(kernel)


if __name__ == "__main__":
    asyncio.run(test_hf_embeddings_with_memories())
