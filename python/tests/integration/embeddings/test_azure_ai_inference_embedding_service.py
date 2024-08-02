# Copyright (c) Microsoft. All rights reserved.


import pytest
from azure.ai.inference.aio import EmbeddingsClient
from azure.core.credentials import AzureKeyCredential

from semantic_kernel.connectors.ai.azure_ai_inference.services.azure_ai_inference_text_embedding import (
    AzureAIInferenceTextEmbedding,
)
from semantic_kernel.connectors.ai.open_ai.settings.azure_open_ai_settings import AzureOpenAISettings
from semantic_kernel.core_plugins.text_memory_plugin import TextMemoryPlugin
from semantic_kernel.kernel import Kernel
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory
from semantic_kernel.memory.volatile_memory_store import VolatileMemoryStore


@pytest.mark.asyncio
async def test_azure_ai_inference_embedding_service(kernel: Kernel):
    # Use an Azure OpenAI deployment for testing
    azure_openai_settings = AzureOpenAISettings.create()
    endpoint = azure_openai_settings.endpoint
    deployment_name = azure_openai_settings.embedding_deployment_name
    api_key = azure_openai_settings.api_key.get_secret_value()

    embeddings_gen = AzureAIInferenceTextEmbedding(
        ai_model_id=deployment_name,
        client=EmbeddingsClient(
            endpoint=f'{str(endpoint).strip("/")}/openai/deployments/{deployment_name}',
            credential=AzureKeyCredential(""),
            headers={"api-key": api_key},
        ),
    )

    kernel.add_service(embeddings_gen)

    memory = SemanticTextMemory(storage=VolatileMemoryStore(), embeddings_generator=embeddings_gen)
    kernel.add_plugin(TextMemoryPlugin(memory), "TextMemoryPlugin")

    await memory.save_information(collection="generic", id="info1", text="My budget for 2024 is $100,000")
    await memory.save_reference(
        "test",
        external_id="info1",
        text="this is a test",
        external_source_name="external source",
    )
