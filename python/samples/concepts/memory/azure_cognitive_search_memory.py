# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureTextCompletion, AzureTextEmbedding
from semantic_kernel.connectors.memory.azure_cognitive_search import AzureCognitiveSearchMemoryStore
from semantic_kernel.connectors.memory.azure_cognitive_search.azure_ai_search_settings import AzureAISearchSettings
from semantic_kernel.core_plugins import TextMemoryPlugin
from semantic_kernel.memory import SemanticTextMemory

COLLECTION_NAME = "acs-index-sample"


async def populate_memory(memory: SemanticTextMemory) -> None:
    # Add some documents to the ACS semantic memory
    await memory.save_information(COLLECTION_NAME, id="info1", text="My name is Andrea")
    await memory.save_information(COLLECTION_NAME, id="info2", text="I currently work as a tour guide")
    await memory.save_information(COLLECTION_NAME, id="info3", text="I've been living in Seattle since 2005")
    await memory.save_information(
        COLLECTION_NAME,
        id="info4",
        text="I visited France and Italy five times since 2015",
    )
    await memory.save_information(COLLECTION_NAME, id="info5", text="My family is from New York")


async def search_acs_memory_questions(memory: SemanticTextMemory) -> None:
    questions = [
        "what's my name",
        "where do I live?",
        "where's my family from?",
        "where have I traveled?",
        "what do I do for work",
    ]

    for question in questions:
        print(f"Question: {question}")
        result = await memory.search(COLLECTION_NAME, question)
        print(f"Answer: {result[0].text}\n")


async def main() -> None:
    kernel = Kernel()

    azure_ai_search_settings = AzureAISearchSettings()

    vector_size = 1536

    # Setting up OpenAI services for text completion and text embedding
    text_complete_service_id = "dv"
    kernel.add_service(
        AzureTextCompletion(
            service_id=text_complete_service_id,
        ),
    )
    embedding_service_id = "ada"
    embedding_gen = AzureTextEmbedding(
        service_id=embedding_service_id,
    )
    kernel.add_service(
        embedding_gen,
    )

    acs_connector = AzureCognitiveSearchMemoryStore(
        vector_size=vector_size,
        search_endpoint=azure_ai_search_settings.endpoint,
        admin_key=azure_ai_search_settings.api_key,
    )

    memory = SemanticTextMemory(storage=acs_connector, embeddings_generator=embedding_gen)
    kernel.add_plugin(TextMemoryPlugin(memory), "TextMemoryPlugin")

    print("Populating memory...")
    await populate_memory(memory)

    print("Asking questions... (manually)")
    await search_acs_memory_questions(memory)

    await acs_connector.close()


if __name__ == "__main__":
    asyncio.run(main())
