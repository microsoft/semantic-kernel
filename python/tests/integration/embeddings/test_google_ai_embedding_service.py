# Copyright (c) Microsoft. All rights reserved.


import pytest

from semantic_kernel.connectors.ai.google.google_ai import GoogleAITextEmbedding
from semantic_kernel.core_plugins.text_memory_plugin import TextMemoryPlugin
from semantic_kernel.kernel import Kernel
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory
from semantic_kernel.memory.volatile_memory_store import VolatileMemoryStore


@pytest.mark.asyncio
async def test_google_ai_embedding_service(kernel: Kernel):
    embeddings_gen = GoogleAITextEmbedding()

    kernel.add_service(embeddings_gen)

    memory = SemanticTextMemory(
        storage=VolatileMemoryStore(), embeddings_generator=embeddings_gen
    )
    kernel.add_plugin(TextMemoryPlugin(memory), "TextMemoryPlugin")

    await memory.save_information(
        collection="generic", id="info1", text="My budget for 2024 is $100,000"
    )
    await memory.save_reference(
        "test",
        external_id="info1",
        text="this is a test",
        external_source_name="external source",
    )
