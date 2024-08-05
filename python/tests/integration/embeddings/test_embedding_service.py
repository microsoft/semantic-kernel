# Copyright (c) Microsoft. All rights reserved.

import os

import pytest

import semantic_kernel as sk
from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.ai.mistral_ai import MistralAITextEmbedding
from semantic_kernel.core_plugins.text_memory_plugin import TextMemoryPlugin
from semantic_kernel.kernel import Kernel
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory

mistral_ai_setup: bool = False
try:
    if os.environ["MISTRALAI_API_KEY"] and os.environ["MISTRALAI_EMBEDDING_MODEL_ID"]:
        mistral_ai_setup = True
except KeyError:
    mistral_ai_setup = False


pytestmark = pytest.mark.parametrize("embeddings_generator",
    [
        pytest.param(
            MistralAITextEmbedding() if mistral_ai_setup else None,
            marks=pytest.mark.skipif(not mistral_ai_setup, reason="Mistral AI environment variables not set"),
            id="MistralEmbeddings"
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

    # Add some documents to the semantic memory
    await memory.save_information("test", id="info1", text="Sharks are fish.")
    await memory.save_information("test", id="info2", text="Whales are mammals.")
    await memory.save_information("test", id="info3", text="Penguins are birds.")
    await memory.save_information("test", id="info4", text="Dolphins are mammals.")
    await memory.save_information("test", id="info5", text="Flies are insects.")

    # Search for documents
    query = "What are mammals?"
    result = await memory.search("test", query, limit=2, min_relevance_score=0.0)
    print(f"Query: {query}")
    print(f"\tAnswer 1: {result[0].text}")
    print(f"\tAnswer 2: {result[1].text}\n")
    assert "mammals." in result[0].text
    assert "mammals." in result[1].text

    query = "What are fish?"
    result = await memory.search("test", query, limit=1, min_relevance_score=0.0)
    print(f"Query: {query}")
    print(f"\tAnswer: {result[0].text}\n")
    assert result[0].text == "Sharks are fish."

    query = "What are insects?"
    result = await memory.search("test", query, limit=1, min_relevance_score=0.0)
    print(f"Query: {query}")
    print(f"\tAnswer: {result[0].text}\n")
    assert result[0].text == "Flies are insects."

    query = "What are birds?"
    result = await memory.search("test", query, limit=1, min_relevance_score=0.0)
    print(f"Query: {query}")
    print(f"\tAnswer: {result[0].text}\n")
    assert result[0].text == "Penguins are birds."
