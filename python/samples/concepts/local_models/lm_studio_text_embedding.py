# Copyright (c) Microsoft. All rights reserved.

import asyncio

from openai import AsyncOpenAI

from semantic_kernel.connectors.ai.open_ai import OpenAITextEmbedding
from semantic_kernel.core_plugins.text_memory_plugin import TextMemoryPlugin
from semantic_kernel.kernel import Kernel
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory
from semantic_kernel.memory.volatile_memory_store import VolatileMemoryStore

# This concept sample shows how to use the OpenAI connector to add memory
# to applications with a local embedding model running in LM studio: https://lmstudio.ai/
# Please follow the instructions here: https://lmstudio.ai/docs/local-server to set up LM studio.
# The default model used in this sample is from nomic.ai due to its compact size.

kernel = Kernel()

service_id = "local-gpt"

openAIClient: AsyncOpenAI = AsyncOpenAI(
    api_key="fake_key",  # This cannot be an empty string, use a fake key
    base_url="http://localhost:1234/v1",
)
kernel.add_service(
    OpenAITextEmbedding(
        service_id=service_id, ai_model_id="Nomic-embed-text-v1.5-Embedding-GGUF", async_client=openAIClient
    )
)

memory = SemanticTextMemory(storage=VolatileMemoryStore(), embeddings_generator=kernel.get_service(service_id))
kernel.add_plugin(TextMemoryPlugin(memory), "TextMemoryPlugin")


async def populate_memory(memory: SemanticTextMemory, collection_id="generic") -> None:
    # Add some documents to the semantic memory
    await memory.save_information(collection=collection_id, id="info1", text="Your budget for 2024 is $100,000")
    await memory.save_information(collection=collection_id, id="info2", text="Your savings from 2023 are $50,000")
    await memory.save_information(collection=collection_id, id="info3", text="Your investments are $80,000")


async def search_memory_examples(memory: SemanticTextMemory, collection_id="generic") -> None:
    questions = [
        "What is my budget for 2024?",
        "What are my savings from 2023?",
        "What are my investments?",
    ]

    for question in questions:
        print(f"Question: {question}")
        result = await memory.search(collection_id, question)
        print(f"Answer: {result[0].text}\n")


async def main() -> None:
    await populate_memory(memory)
    await search_memory_examples(memory)


if __name__ == "__main__":
    asyncio.run(main())
