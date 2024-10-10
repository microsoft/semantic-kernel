# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.connectors.ai.bedrock.services.bedrock_text_embedding import BedrockTextEmbedding
from semantic_kernel.core_plugins.text_memory_plugin import TextMemoryPlugin
from semantic_kernel.kernel import Kernel
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory
from semantic_kernel.memory.volatile_memory_store import VolatileMemoryStore


@pytest.mark.asyncio
@pytest.mark.parametrize(
    # These are fake model ids with the supported prefixes
    "model_id",
    [
        "amazon.titan-embed-text-v1",
        "amazon.titan-embed-text-v2:0",
        "cohere.embed-english-v3",
    ],
)
async def test_bedrock_embedding_service(model_id: str, kernel: Kernel):
    embeddings_gen = BedrockTextEmbedding(model_id=model_id)

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
