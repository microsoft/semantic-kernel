# Copyright (c) Microsoft. All rights reserved.

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Annotated
from uuid import uuid4

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAITextEmbedding
from semantic_kernel.connectors.in_memory import InMemoryStore
from semantic_kernel.data.vector import VectorStore, VectorStoreCollection, VectorStoreField, vectorstoremodel
from semantic_kernel.filters import FilterTypes, FunctionInvocationContext, PromptRenderContext
from semantic_kernel.functions import FunctionResult

COLLECTION_NAME = "llm_responses"
RECORD_ID_KEY = "cache_record_id"


# Define a simple data model to store, the prompt and the result
# we annotate the prompt field as the vector field, the prompt itself will not be stored.
# and if you use `include_vectors` in the search, it will return the vector, but not the prompt.
@vectorstoremodel(collection_name=COLLECTION_NAME)
@dataclass
class CacheRecord:
    result: Annotated[str, VectorStoreField("data", is_full_text_indexed=True)]
    prompt: Annotated[str | None, VectorStoreField("vector", dimensions=1536)] = None
    id: Annotated[str, VectorStoreField("key")] = field(default_factory=lambda: str(uuid4()))


# Define the filters, one for caching the results and one for using the cache.
class PromptCacheFilter:
    """A filter to cache the results of the prompt rendering and function invocation."""

    def __init__(
        self,
        vector_store: VectorStore,
        score_threshold: float = 0.2,
    ):
        if vector_store.embedding_generator is None:
            raise ValueError("The vector store must have an embedding generator.")
        self.vector_store = vector_store
        self.collection: VectorStoreCollection[str, CacheRecord] = vector_store.get_collection(record_type=CacheRecord)
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
        await self.collection.ensure_collection_exists()
        results = await self.collection.search(context.rendered_prompt, vector_property_name="prompt", top=1)
        async for result in results.results:
            if result.score and result.score < self.score_threshold:
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
            cache_record = CacheRecord(prompt=result.rendered_prompt, result=str(result))
            await self.collection.ensure_collection_exists()
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
    # create the in-memory vector store
    vector_store = InMemoryStore(embedding_generator=embedding)
    # create the cache filter and add the filters to the kernel
    cache = PromptCacheFilter(vector_store=vector_store)
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
