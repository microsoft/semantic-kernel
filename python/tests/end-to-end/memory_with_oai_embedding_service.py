# Copyright (c) Microsoft. All rights reserved.

import asyncio

from utils import e2e_memories

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai

kernel = sk.Kernel()

# Load credentials from .env file
api_key, org_id = sk.openai_settings_from_dot_env()

kernel.add_embedding_service(
    "ada", sk_oai.OpenAITextEmbedding("text-embedding-ada-002", api_key, org_id)
)
kernel.register_memory_store(memory_store=sk.memory.VolatileMemoryStore())

asyncio.run(e2e_memories.simple_memory_test(kernel))
