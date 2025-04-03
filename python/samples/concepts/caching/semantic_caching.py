# Copyright (c) Microsoft. All rights reserved.

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Annotated
from uuid import uuid4

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAITextEmbedding
from semantic_kernel.connectors.memory.in_memory.in_memory_store import InMemoryVectorStore
from semantic_kernel.data import (
    VectorizedSearchMixin,
    VectorSearchOptions,
    VectorStore,
    VectorStoreRecordCollection,
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
    vectorstoremodel,
)
from semantic_kernel.filters import FilterTypes, FunctionInvocationContext, PromptRenderContext
from semantic_kernel.functions import FunctionResult

COLLECTION_NAME = "llm_responses"
RECORD_ID_KEY = "cache_record_id"


# Define a simple data model to store, the prompt, the result, and the prompt embedding.
@vectorstoremodel
@dataclass
class CacheRecord:
    prompt: Annotated[str, VectorStoreRecordDataField(embedding_property_name="prompt_embedding")]
    result: Annotated[str, VectorStoreRecordDataField(is_full_text_searchable=True)]
    prompt_embedding: Annotated[list[float], VectorStoreRecordVectorField(dimensions=1536)] = field(
        default_factory=list
    )
    id: Annotated[str, VectorStoreRecordKeyField] = field(default_factory=lambda: str(uuid4()))


# Define the filters, one for caching the results and one for using the cache.
class PromptCacheFilter:
    """A filter to cache the results of the prompt rendering and function invocation."""

    def __init__(
        self,
        embedding_service: EmbeddingGeneratorBase,
        vector_store: VectorStore,
        collection_name: str = COLLECTION_NAME,
        score_threshold: float = 0.2,
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.collection: VectorStoreRecordCollection[str, CacheRecord] = vector_store.get_collection(
            collection_name, data_model_type=CacheRecord
        )
        self.score_threshold = score_threshold

    async def on_prompt_render(
        self, context: PromptRenderContext, next: Callable[[PromptRenderContext], Awaitable[None]]
    ):
        """Filter to cache the rendered prompt and the result of the function.

        It uses the score threshold to determine if the result should be cached.
        The direction of the comparison is based on the default distance metric for
        the in memory vector store, which is cosine distance, so the closer to 0 the
        closer the match.
        """
        await next(context)
        assert context.rendered_prompt  # nosec
        prompt_embedding = await self.embedding_service.generate_raw_embeddings([context.rendered_prompt])
        await self.collection.create_collection_if_not_exists()
        assert isinstance(self.collection, VectorizedSearchMixin)  # nosec
        results = await self.collection.vectorized_search(
            vector=prompt_embedding[0], options=VectorSearchOptions(vector_field_name="prompt_embedding", top=1)
        )
        async for result in results.results:
            if result.score < self.score_threshold:
                context.function_result = FunctionResult(
                    function=context.function.metadata,
                    value=result.record.result,
                    rendered_prompt=context.rendered_prompt,
                    metadata={RECORD_ID_KEY: result.record.id},
                )

    async def on_function_invocation(
        self, context: FunctionInvocationContext, next: Callable[[FunctionInvocationContext], Awaitable[None]]
    ):
        """Filter to store the result in the cache if it is new."""
        await next(context)
        result = context.result
        if result and result.rendered_prompt and RECORD_ID_KEY not in result.metadata:
            prompt_embedding = await self.embedding_service.generate_embeddings([result.rendered_prompt])
            cache_record = CacheRecord(
                prompt=result.rendered_prompt,
                result=str(result),
                prompt_embedding=prompt_embedding[0],
            )
            await self.collection.create_collection_if_not_exists()
            await self.collection.upsert(cache_record)


async def execute_async(kernel: Kernel, title: str, prompt: str):
    """Helper method to execute and log time."""
    print(f"{title}: {prompt}")
    start = time.time()
    result = await kernel.invoke_prompt(prompt)
    elapsed = time.time() - start
    print(f"\tElapsed Time: {elapsed:.3f}")
    return result


async def main():
    # create the kernel and add the chat service and the embedding service
    kernel = Kernel()
    chat = OpenAIChatCompletion(service_id="default")
    embedding = OpenAITextEmbedding(service_id="embedder")
    kernel.add_service(chat)
    kernel.add_service(embedding)
    # create the in-memory vector store
    vector_store = InMemoryVectorStore()
    # create the cache filter and add the filters to the kernel
    cache = PromptCacheFilter(embedding_service=embedding, vector_store=vector_store)
    kernel.add_filter(FilterTypes.PROMPT_RENDERING, cache.on_prompt_render)
    kernel.add_filter(FilterTypes.FUNCTION_INVOCATION, cache.on_function_invocation)

    # Run the sample
    print("\nIn-memory cache sample:")
    r1 = await execute_async(kernel, "First run", "What's the tallest building in New York?")
    print(f"\tResult 1: {r1}")
    r2 = await execute_async(kernel, "Second run", "How are you today?")
    print(f"\tResult 2: {r2}")
    r3 = await execute_async(kernel, "Third run", "What is the highest building in New York City?")
    print(f"\tResult 3: {r3}")


if __name__ == "__main__":
    asyncio.run(main())
