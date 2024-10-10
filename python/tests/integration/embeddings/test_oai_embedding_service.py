# Copyright (c) Microsoft. All rights reserved.

import pytest
from openai import AsyncOpenAI

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.open_ai.settings.open_ai_settings import (
    OpenAISettings,
)
from semantic_kernel.core_plugins.text_memory_plugin import TextMemoryPlugin
from semantic_kernel.kernel import Kernel
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory


@pytest.mark.asyncio
async def test_oai_embedding_service(kernel: Kernel):
    embedding_gen = sk_oai.OpenAITextEmbedding(
        service_id="oai-ada",
        ai_model_id="text-embedding-ada-002",
    )

    kernel.add_service(embedding_gen)

<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
    memory = SemanticTextMemory(
        storage=sk.memory.VolatileMemoryStore(), embeddings_generator=embedding_gen
    )
    kernel.add_plugin(TextMemoryPlugin(memory), "TextMemoryPlugin")

<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
    memory = SemanticTextMemory(
        storage=sk.memory.VolatileMemoryStore(), embeddings_generator=embedding_gen
    )
    kernel.add_plugin(TextMemoryPlugin(memory), "TextMemoryPlugin")
=======
    embedding_gen = sk_oai.OpenAITextEmbedding(
        service_id="oai-ada", ai_model_id="text-embedding-ada-002", api_key=api_key, org_id=org_id
    )

    kernel.add_service(embedding_gen)
    kernel.use_memory(storage=sk.memory.VolatileMemoryStore(), embeddings_generator=embedding_gen)
>>>>>>> ms/small_fixes

>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    await memory.save_reference(
        "test",
        external_id="info1",
        text="this is a test",
        external_source_name="external source",
    )

=======
<<<<<<< main
    memory = SemanticTextMemory(
        storage=sk.memory.VolatileMemoryStore(), embeddings_generator=embedding_gen
    )
    kernel.add_plugin(TextMemoryPlugin(memory), "TextMemoryPlugin")
=======
    embedding_gen = sk_oai.OpenAITextEmbedding(
        service_id="oai-ada", ai_model_id="text-embedding-ada-002", api_key=api_key, org_id=org_id
    )

    kernel.add_service(embedding_gen)
    kernel.use_memory(storage=sk.memory.VolatileMemoryStore(), embeddings_generator=embedding_gen)
>>>>>>> ms/small_fixes

=======
>>>>>>> Stashed changes
    await memory.save_reference(
        "test",
        external_id="info1",
        text="this is a test",
        external_source_name="external source",
    )

<<<<<<< Updated upstream
>>>>>>> origin/main
=======
>>>>>>> Stashed changes

@pytest.mark.asyncio
async def test_oai_embedding_service_with_provided_client(kernel: Kernel):
    openai_settings = OpenAISettings.create()
    api_key = openai_settings.api_key.get_secret_value()
    org_id = openai_settings.org_id

    client = AsyncOpenAI(
        api_key=api_key,
        organization=org_id,
    )

    embedding_gen = sk_oai.OpenAITextEmbedding(
        service_id="oai-ada", ai_model_id="text-embedding-ada-002", async_client=client
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< main
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
    )

    kernel.add_service(embedding_gen)
    memory = SemanticTextMemory(
        storage=sk.memory.VolatileMemoryStore(), embeddings_generator=embedding_gen
    )
    kernel.add_plugin(TextMemoryPlugin(memory), "TextMemoryPlugin")
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> origin/main
=======
=======
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
    )

    kernel.add_service(embedding_gen)
    kernel.use_memory(storage=sk.memory.VolatileMemoryStore(), embeddings_generator=embedding_gen)
>>>>>>> ms/small_fixes
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main

    await memory.save_reference(
        "test",
        external_id="info1",
        text="this is a test",
        external_source_name="external source",
    )
