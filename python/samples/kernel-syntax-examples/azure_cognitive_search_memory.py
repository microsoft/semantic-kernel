# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

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

    # Add OpenAI services
    (
        open_ai_deployment,
        open_api_key,
        open_ai_endpoint,
    ) = sk.azure_openai_settings_from_dot_env()

    # Setting up OpenAI services for text completion and text embedding
    kernel.add_text_completion_service(
        "dv",
        AzureTextCompletion(
            deployment_name=open_ai_deployment,
            endpoint=open_ai_endpoint,
            api_key=open_api_key,
        ),
    )
    kernel.add_text_embedding_generation_service(
        "ada",
        AzureTextEmbedding(
            deployment_name=open_ai_deployment,
            endpoint=open_ai_endpoint,
            api_key=open_api_key,
        ),
    )

    ACS_ENDPOINT = os.environ["AZURE_ACS_ENDPOINT"]
    ACS_ADMIN_KEY = os.environ["AZURE_ACS_ADMIN_KEY"]
    vector_size = 1536

    connector = AzureCognitiveSearchMemoryStore(
        vector_size, ACS_ENDPOINT, ACS_ADMIN_KEY
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
