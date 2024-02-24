# Copyright (c) Microsoft. All rights reserved.

import os

import pytest
from openai import AsyncAzureOpenAI

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai


@pytest.mark.asyncio
async def test_azure_text_embedding_service(create_kernel, get_aoai_config):
    kernel = create_kernel

    _, api_key, endpoint = get_aoai_config

    if "Python_Integration_Tests" in os.environ:
        deployment_name = os.environ["AzureOpenAIEmbeddings_EastUS__DeploymentName"]
    else:
        deployment_name = "text-embedding-ada-002"

    embeddings_gen = sk_oai.AzureTextEmbedding(
        service_id="aoai-ada",
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
    )

    kernel.add_service(embeddings_gen)

    kernel.use_memory(storage=sk.memory.VolatileMemoryStore(), embeddings_generator=embeddings_gen)

    await kernel.memory.save_information("test", id="info1", text="this is a test")
    await kernel.memory.save_reference(
        "test",
        external_id="info1",
        text="this is a test",
        external_source_name="external source",
    )


@pytest.mark.asyncio
async def test_azure_text_embedding_service_with_provided_client(create_kernel, get_aoai_config):
    kernel = create_kernel

    _, api_key, endpoint = get_aoai_config

    if "Python_Integration_Tests" in os.environ:
        deployment_name = os.environ["AzureOpenAIEmbeddings_EastUS__DeploymentName"]
    else:
        deployment_name = "text-embedding-ada-002"

    client = AsyncAzureOpenAI(
        azure_endpoint=endpoint,
        azure_deployment=deployment_name,
        api_key=api_key,
        api_version="2023-05-15",
        default_headers={"Test-User-X-ID": "test"},
    )

    embedding_gen = sk_oai.AzureTextEmbedding(
        service_id="aoai-ada-2",
        deployment_name=deployment_name,
        async_client=client,
    )

    kernel.add_service(embedding_gen)
    kernel.use_memory(storage=sk.memory.VolatileMemoryStore(), embeddings_generator=embedding_gen)

    await kernel.memory.save_information("test", id="info1", text="this is a test")
    await kernel.memory.save_reference(
        "test",
        external_id="info1",
        text="this is a test",
        external_source_name="external source",
    )


@pytest.mark.asyncio
async def test_batch_azure_embeddings(get_aoai_config):
    # Configure LLM service
    _, api_key, endpoint = get_aoai_config

    if "Python_Integration_Tests" in os.environ:
        deployment_name = os.environ["AzureOpenAIEmbeddings_EastUS__DeploymentName"]

    else:
        deployment_name = "text-embedding-ada-002"

    embeddings_service = sk_oai.AzureTextEmbedding(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
    )
    texts = ["hello world"]
    results = await embeddings_service.generate_embeddings(texts)
    batch_results = await embeddings_service.generate_embeddings(texts, batch_size=1)
    assert len(results) == len(batch_results)
