# Copyright (c) Microsoft. All rights reserved.

import asyncio

from utils import e2e_memories

import semantic_kernel as sk
import semantic_kernel.connectors.ai.hugging_face as sk_hf

kernel = sk.Kernel()

# Configure LLM service
kernel.add_embedding_service(
    "sentence-transformers/all-MiniLM-L6-v2",
    sk_hf.HuggingFaceTextEmbedding("sentence-transformers/all-MiniLM-L6-v2"),
)
kernel.register_memory_store(memory_store=sk.memory.VolatileMemoryStore())

asyncio.run(e2e_memories.simple_memory_test(kernel))
