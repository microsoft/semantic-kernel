# Copyright (c) Microsoft. All rights reserved.

import pytest

import semantic_kernel as sk
from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.ai.mistral_ai import MistralAITextEmbedding
from semantic_kernel.connectors.ai.open_ai import OpenAITextEmbedding
from semantic_kernel.core_plugins.text_memory_plugin import TextMemoryPlugin
from semantic_kernel.kernel import Kernel
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory

pytestmark = pytest.mark.parametrize("embeddings_generator",
    [
        pytest.param(
            MistralAITextEmbedding(),
            id="MistralEmbeddings"
        ),
        pytest.param(
            OpenAITextEmbedding(ai_model_id="text-embedding-ada-002"),
            id="OpenAIEmbeddings"
        )
    ]
)


@pytest.mark.asyncio(scope="module")
async def test_embedding_service(kernel: Kernel, embeddings_generator: EmbeddingGeneratorBase):
    kernel.add_service(embeddings_generator)

    memory = SemanticTextMemory(storage=sk.memory.VolatileMemoryStore(), embeddings_generator=embeddings_generator)
    kernel.add_plugin(TextMemoryPlugin(memory), "TextMemoryPlugin")

    await memory.save_reference(
        "test",
        external_id="info1",
        text="this is a test",
        external_source_name="external source",
    )
