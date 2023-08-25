# Copyright (c) Microsoft. All rights reserved.

import asyncio

from dotenv import dotenv_values

import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import (
    AzureTextCompletion,
    AzureTextEmbedding,
)
from semantic_kernel.connectors.memory.azure_cognitive_search import (
    AzureCognitiveSearchMemoryStore,
)

COLLECTION_NAME = "acs-index-sample"


async def populate_memory(kernel: sk.Kernel) -> None:
    # Add some documents to the ACS semantic memory
    await kernel.memory.save_information_async(
        COLLECTION_NAME, id="info1", text="My name is Andrea"
    )
    await kernel.memory.save_information_async(
        COLLECTION_NAME, id="info2", text="I currently work as a tour guide"
    )
    await kernel.memory.save_information_async(
        COLLECTION_NAME, id="info3", text="I've been living in Seattle since 2005"
    )
    await kernel.memory.save_information_async(
        COLLECTION_NAME,
        id="info4",
        text="I visited France and Italy five times since 2015",
    )
    await kernel.memory.save_information_async(
        COLLECTION_NAME, id="info5", text="My family is from New York"
    )


async def search_acs_memory_questions(kernel: sk.Kernel) -> None:
    questions = [
        "what's my name",
        "where do I live?",
        "where's my family from?",
        "where have I traveled?",
        "what do I do for work",
    ]

    for question in questions:
        print(f"Question: {question}")
        result = await kernel.memory.search_async(COLLECTION_NAME, question)
        print(f"Answer: {result[0].text}\n")


async def main() -> None:
    kernel = sk.Kernel()

    config = dotenv_values(".env")

    AZURE_COGNITIVE_SEARCH_ENDPOINT = config["AZURE_COGNITIVE_SEARCH_ENDPOINT"]
    AZURE_COGNITIVE_SEARCH_ADMIN_KEY = config["AZURE_COGNITIVE_SEARCH_ADMIN_KEY"]
    AZURE_OPENAI_API_KEY = config["AZURE_OPENAI_API_KEY"]
    AZURE_OPENAI_ENDPOINT = config["AZURE_OPENAI_ENDPOINT"]
    vector_size = 1536

    # Setting up OpenAI services for text completion and text embedding
    kernel.add_text_completion_service(
        "dv",
        AzureTextCompletion(
            deployment_name="text-embedding-ada-002",
            endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_API_KEY,
        ),
    )
    kernel.add_text_embedding_generation_service(
        "ada",
        AzureTextEmbedding(
            deployment_name="text-embedding-ada-002",
            endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_API_KEY,
        ),
    )

    connector = AzureCognitiveSearchMemoryStore(
        vector_size, AZURE_COGNITIVE_SEARCH_ENDPOINT, AZURE_COGNITIVE_SEARCH_ADMIN_KEY
    )

    # Register the memory store with the kernel
    kernel.register_memory_store(memory_store=connector)

    print("Populating memory...")
    await populate_memory(kernel)

    print("Asking questions... (manually)")
    await search_acs_memory_questions(kernel)

    await connector.close_async()


if __name__ == "__main__":
    asyncio.run(main())
