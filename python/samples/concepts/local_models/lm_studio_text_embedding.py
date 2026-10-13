# Copyright (c) Microsoft. All rights reserved.

import asyncio
from dataclasses import dataclass
from typing import Annotated

from openai import AsyncOpenAI

from semantic_kernel.connectors.ai.open_ai import OpenAITextEmbedding
from semantic_kernel.connectors.in_memory import InMemoryCollection
from semantic_kernel.data.vector import VectorStoreField, vectorstoremodel

# This concept sample shows how to use a local embedding model running in LM Studio:
# https://lmstudio.ai/. Please follow the instructions here to set up the local server:
# https://lmstudio.ai/docs/local-server. The default model is Nomic Embed Text v1.5.


@vectorstoremodel(collection_name="generic")
@dataclass
class MemoryRecord:
    content: Annotated[str, VectorStoreField("data")]
    id: Annotated[str, VectorStoreField("key")]
    embedding: Annotated[list[float] | str | None, VectorStoreField("vector", dimensions=768)] = None

    def __post_init__(self) -> None:
        if self.embedding is None:
            # Vector collections generate an embedding from this text during upsert.
            self.embedding = self.content


async def populate_memory(collection: InMemoryCollection[str, MemoryRecord]) -> None:
    """Add a few example documents to the in-memory vector collection."""
    await collection.upsert([
        MemoryRecord(id="info1", content="Your budget for 2024 is $100,000"),
        MemoryRecord(id="info2", content="Your savings from 2023 are $50,000"),
        MemoryRecord(id="info3", content="Your investments are $80,000"),
    ])


async def search_memory_examples(collection: InMemoryCollection[str, MemoryRecord]) -> None:
    """Search the vector collection with questions embedded by LM Studio."""
    questions = [
        "What is my budget for 2024?",
        "What are my savings from 2023?",
        "What are my investments?",
    ]

    for question in questions:
        print(f"Question: {question}")
        results = await collection.search(values=question, vector_property_name="embedding", top=1)
        async for result in results.results:
            print(f"Answer: {result.record.content}\n")


async def main() -> None:
    openai_client = AsyncOpenAI(
        api_key="fake_key",  # LM Studio's local server does not require a real key.
        base_url="http://localhost:1234/v1",
    )
    embedder = OpenAITextEmbedding(
        service_id="local-embedding",
        ai_model_id="Nomic-embed-text-v1.5-Embedding-GGUF",
        async_client=openai_client,
    )

    try:
        async with InMemoryCollection[str, MemoryRecord](
            record_type=MemoryRecord,
            embedding_generator=embedder,
        ) as collection:
            await collection.ensure_collection_exists()
            await populate_memory(collection)
            await search_memory_examples(collection)
    finally:
        await openai_client.close()


if __name__ == "__main__":
    asyncio.run(main())
