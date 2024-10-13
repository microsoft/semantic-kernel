# Copyright (c) Microsoft. All rights reserved.


import pytest
from openai import AsyncAzureOpenAI

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.open_ai.settings.azure_open_ai_settings import (
    AzureOpenAISettings,
)
from semantic_kernel.core_plugins.text_memory_plugin import TextMemoryPlugin
from semantic_kernel.kernel import Kernel
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory
from semantic_kernel.memory.volatile_memory_store import VolatileMemoryStore


@pytest.mark.asyncio
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
async def test_azure_text_embedding_service(kernel: Kernel):
    embeddings_gen = sk_oai.AzureTextEmbedding(
        service_id="aoai-ada",
    )
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
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
async def test_azure_text_embedding_service(kernel: Kernel):
    embeddings_gen = sk_oai.AzureTextEmbedding(
        service_id="aoai-ada",
=======
<<<<<<< div
=======
>>>>>>> main
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
async def test_azure_text_embedding_service(kernel: Kernel):
    embeddings_gen = sk_oai.AzureTextEmbedding(
        service_id="aoai-ada",
    )
=======
async def test_azure_text_embedding_service(create_kernel, get_aoai_config):
    kernel = create_kernel

    _, api_key, endpoint = get_aoai_config

    if "Python_Integration_Tests" in os.environ:
        deployment_name = os.environ["AzureOpenAIEmbeddings__DeploymentName"]
    else:
        deployment_name = "text-embedding-ada-002"

    embeddings_gen = sk_oai.AzureTextEmbedding(
        service_id="aoai-ada",
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
>>>>>>> origin/main
    )

    kernel.add_service(embeddings_gen)

<<<<<<< main
    memory = SemanticTextMemory(
        storage=VolatileMemoryStore(), embeddings_generator=embeddings_gen
    )
    kernel.add_plugin(TextMemoryPlugin(memory), "TextMemoryPlugin")

    await memory.save_information(
        collection="generic", id="info1", text="My budget for 2024 is $100,000"
    )
=======
    kernel.use_memory(storage=sk.memory.VolatileMemoryStore(), embeddings_generator=embeddings_gen)
>>>>>>> ms/small_fixes
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

    kernel.add_service(embeddings_gen)

    memory = SemanticTextMemory(
        storage=VolatileMemoryStore(), embeddings_generator=embeddings_gen
    )
    kernel.add_plugin(TextMemoryPlugin(memory), "TextMemoryPlugin")

    await memory.save_information(
        collection="generic", id="info1", text="My budget for 2024 is $100,000"
    )
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
    )

    kernel.add_service(embeddings_gen)

    kernel.use_memory(storage=sk.memory.VolatileMemoryStore(), embeddings_generator=embeddings_gen)
>>>>>>> ms/small_fixes
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head

    kernel.add_service(embeddings_gen)

    memory = SemanticTextMemory(
        storage=VolatileMemoryStore(), embeddings_generator=embeddings_gen
    )
    kernel.add_plugin(TextMemoryPlugin(memory), "TextMemoryPlugin")

    await memory.save_information(
        collection="generic", id="info1", text="My budget for 2024 is $100,000"
    )
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
>>>>>>> head
    await memory.save_reference(
        "test",
        external_id="info1",
        text="this is a test",
        external_source_name="external source",
    )


@pytest.mark.asyncio
async def test_azure_text_embedding_service_with_provided_client(kernel: Kernel):
    azure_openai_settings = AzureOpenAISettings.create()
    endpoint = azure_openai_settings.endpoint
    deployment_name = azure_openai_settings.embedding_deployment_name
    ad_token = azure_openai_settings.get_azure_openai_auth_token()
    api_version = azure_openai_settings.api_version
<<<<<<< div
<<<<<<< div
=======
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
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
<<<<<<< main
=======
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
<<<<<<< div
=======
>>>>>>> main
=======
>>>>>>> Stashed changes
>>>>>>> head

    client = AsyncAzureOpenAI(
        azure_endpoint=endpoint,
        azure_deployment=deployment_name,
        azure_ad_token=ad_token,
        api_version=api_version,
        default_headers={"Test-User-X-ID": "test"},
    )

<<<<<<< main
    embeddings_gen = sk_oai.AzureTextEmbedding(
        service_id="aoai-ada-2",
        async_client=client,
    )
=======
    embedding_gen = sk_oai.AzureTextEmbedding(
        service_id="aoai-ada-2",
        deployment_name=deployment_name,
        async_client=client,
    )

    kernel.add_service(embedding_gen)
    kernel.use_memory(storage=sk.memory.VolatileMemoryStore(), embeddings_generator=embedding_gen)
>>>>>>> ms/small_fixes

    kernel.add_service(embeddings_gen)
    memory = SemanticTextMemory(
        storage=sk.memory.VolatileMemoryStore(), embeddings_generator=embeddings_gen
    )
    kernel.add_plugin(TextMemoryPlugin(memory), "TextMemoryPlugin")

    await memory.save_information(
        collection="generic", id="info1", text="My budget for 2024 is $100,000"
    )
    await memory.save_reference(
        "test",
        external_id="info1",
        text="this is a test",
        external_source_name="external source",
    )


@pytest.mark.asyncio
async def test_batch_azure_embeddings():
    # Configure LLM service
<<<<<<< main
    embeddings_service = sk_oai.AzureTextEmbedding(service_id="aoai-ada")
=======
    _, api_key, endpoint = get_aoai_config
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
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
>>>>>>> Stashed changes

    client = AsyncAzureOpenAI(
        azure_endpoint=endpoint,
        azure_deployment=deployment_name,
        azure_ad_token=ad_token,
        api_version=api_version,
        default_headers={"Test-User-X-ID": "test"},
    )

    embeddings_gen = sk_oai.AzureTextEmbedding(
        service_id="aoai-ada-2",
        async_client=client,
    )

    kernel.add_service(embeddings_gen)
    memory = SemanticTextMemory(
        storage=sk.memory.VolatileMemoryStore(), embeddings_generator=embeddings_gen
    )
    kernel.add_plugin(TextMemoryPlugin(memory), "TextMemoryPlugin")

    await memory.save_information(
        collection="generic", id="info1", text="My budget for 2024 is $100,000"
    )
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
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
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
    await memory.save_reference(
        "test",
        external_id="info1",
        text="this is a test",
        external_source_name="external source",
    )


@pytest.mark.asyncio
async def test_batch_azure_embeddings():
    # Configure LLM service
    embeddings_service = sk_oai.AzureTextEmbedding(service_id="aoai-ada")
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
=======
>>>>>>> ms/small_fixes
>>>>>>> origin/main
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
=======
>>>>>>> ms/small_fixes
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
=======
>>>>>>> ms/small_fixes
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
=======
>>>>>>> ms/small_fixes
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
=======
>>>>>>> ms/small_fixes
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
=======
>>>>>>> ms/small_fixes
>>>>>>> origin/main
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> ms/small_fixes
>>>>>>> main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> ms/small_fixes
>>>>>>> origin/main
>>>>>>> head
    texts = ["hello world"]
    results = await embeddings_service.generate_embeddings(texts)
    batch_results = await embeddings_service.generate_embeddings(texts, batch_size=1)
    assert len(results) == len(batch_results)
