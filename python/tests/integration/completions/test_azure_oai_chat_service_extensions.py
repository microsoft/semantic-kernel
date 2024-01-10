# Copyright (c) Microsoft. All rights reserved.

import os
import time
from random import randint

import numpy as np
import pytest

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.open_ai.request_settings.azure_chat_request_settings import (
    AzureAISearchDataSources,
    AzureChatRequestSettings,
    AzureDataSources,
    ExtraBody,
)
from semantic_kernel.connectors.memory.azure_cognitive_search.azure_cognitive_search_memory_store import (
    AzureCognitiveSearchMemoryStore,
)
from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.semantic_functions.chat_prompt_template import ChatPromptTemplate

try:
    azure_cognitive_search_installed = True
except ImportError:
    azure_cognitive_search_installed = False

pytestmark = pytest.mark.skipif(
    not azure_cognitive_search_installed,
    reason="Azure Cognitive Search is not installed",
)


@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def create_memory_store():
    # Create an index and populate it with some data
    collection = f"int-tests-{randint(1000, 9999)}"
    memory_store = AzureCognitiveSearchMemoryStore(vector_size=4)
    await memory_store.create_collection_async(collection)
    time.sleep(1)
    try:
        assert await memory_store.does_collection_exist_async(collection)
        rec = MemoryRecord(
            is_reference=False,
            external_source_name=None,
            id=None,
            description="Emily and David's story.",
            text="Emily and David, two passionate scientists, met during a research expedition to Antarctica. \
                    Bonded by their love for the natural world and shared curiosity, they uncovered a \
                    groundbreaking phenomenon in glaciology that could potentially reshape our understanding \
                    of climate change.",
            additional_metadata=None,
            embedding=np.array([0.2, 0.1, 0.2, 0.7]),
        )
        await memory_store.upsert_async(collection, rec)
        time.sleep(1)
        return collection, memory_store
    except:
        await memory_store.delete_collection_async(collection)
        raise


@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def create_with_data_chat_function(get_aoai_config, create_kernel, create_memory_store):
    collection, memory_store = await create_memory_store
    try:
        deployment_name, api_key, endpoint = get_aoai_config

        if "Python_Integration_Tests" in os.environ:
            deployment_name = os.environ["AzureOpenAIChat__DeploymentName"]
        else:
            deployment_name = "gpt-35-turbo"

        print("* Service: Azure OpenAI Chat Completion")
        print(f"* Endpoint: {endpoint}")
        print(f"* Deployment: {deployment_name}")

        kernel = create_kernel

        # Load Azure OpenAI with data settings
        search_endpoint = os.getenv("AZURE_COGNITIVE_SEARCH_ENDPOINT")
        search_api_key = os.getenv("AZURE_COGNITIVE_SEARCH_ADMIN_KEY")

        extra = ExtraBody(
            data_sources=[
                AzureDataSources(
                    type="AzureCognitiveSearch",
                    parameters=AzureAISearchDataSources(
                        indexName=collection,
                        endpoint=search_endpoint,
                        key=search_api_key,
                    ),
                )
            ]
        )

        chat_service = sk_oai.AzureChatCompletion(
            deployment_name=deployment_name,
            api_key=api_key,
            endpoint=endpoint,
            api_version="2023-12-01-preview",
            use_extensions=True,
        )
        kernel.add_chat_service("chat-gpt", chat_service)

        prompt_config = ChatPromptTemplate(
            completion=AzureChatRequestSettings(
                max_tokens=2000,
                temperature=0.7,
                top_p=0.8,
                extra_body=extra,
            )
        )

        prompt_template = sk.ChatPromptTemplate("{{$user_input}}", kernel.prompt_template_engine, prompt_config)

        function_config = sk.SemanticFunctionConfig(prompt_config, prompt_template)
        chat_function = kernel.register_semantic_function("ChatBot", "Chat", function_config)
        return chat_function, kernel, collection, memory_store
    except:
        await memory_store.delete_collection_async(collection)
        raise


@pytest.mark.asyncio
@pytest.mark.skip
async def test_azure_e2e_chat_completion_with_extensions(
    create_with_data_chat_function,
):
    # Create an index and populate it with some data
    (
        chat_function,
        kernel,
        collection,
        memory_store,
    ) = await create_with_data_chat_function

    try:
        result = []
        async for message in kernel.run_stream_async(chat_function, input_str="who are Emily and David?"):
            result.append(message)
            print(message, end="")
        output = "".join(result).strip()

        print(f"Answer using input string: '{output}'")
        assert len(result) > 1

        await memory_store.delete_collection_async(collection)
    except:
        await memory_store.delete_collection_async(collection)
        raise
