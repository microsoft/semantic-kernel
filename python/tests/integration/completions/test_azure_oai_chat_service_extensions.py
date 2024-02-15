# Copyright (c) Microsoft. All rights reserved.

import os
import time
from random import randint

import numpy as np
import pytest

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureAISearchDataSources,
    AzureChatPromptExecutionSettings,
    AzureDataSources,
    ExtraBody,
)
from semantic_kernel.memory.memory_record import MemoryRecord

try:
    from semantic_kernel.connectors.memory.azure_cognitive_search.azure_cognitive_search_memory_store import (
        AzureCognitiveSearchMemoryStore,
    )

    if os.environ.get("AZURE_COGNITIVE_SEARCH_ENDPOINT") and os.environ.get("AZURE_COGNITIVE_SEARCH_ADMIN_KEY"):
        azure_cognitive_search_installed = True
    else:
        azure_cognitive_search_installed = False
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
    collection = f"int-tests-chat-extensions-{randint(1000, 9999)}"
    memory_store = AzureCognitiveSearchMemoryStore(vector_size=4)
    await memory_store.create_collection(collection)
    time.sleep(1)
    try:
        assert await memory_store.does_collection_exist(collection)
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
        await memory_store.upsert(collection, rec)
        time.sleep(1)
        return collection, memory_store
    except:
        await memory_store.delete_collection(collection)
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
                        queryType="simple",
                        fieldsMapping={
                            "titleField": "Description",
                            "contentFields": ["Text"],
                        },
                        topNDocuments=1,
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
        kernel.add_chat_service("chat-gpt-extensions", chat_service)

        prompt_config = sk.PromptTemplateConfig(
            execution_settings=AzureChatPromptExecutionSettings(
                max_tokens=2000,
                temperature=0.7,
                top_p=0.8,
                extra_body=extra,
            )
        )
        prompt_config.default_services = ["chat-gpt-extensions"]

        prompt_template = sk.ChatPromptTemplate("{{$input}}", kernel.prompt_template_engine, prompt_config)

        function_config = sk.SemanticFunctionConfig(prompt_config, prompt_template)
        chat_function = kernel.register_semantic_function("ChatBot", "Chat", function_config)
        return chat_function, kernel, collection, memory_store
    except:
        await memory_store.delete_collection(collection)
        raise


@pytest.mark.asyncio
@pytestmark
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
        result = None
        async for message in kernel.run_stream(chat_function, input_str="who are Emily and David?"):
            result = message[0] if not result else result + message[0]
            print(message, end="")

        print(f"Answer using input string: '{result}'")
        print(f"Tool message: {result.tool_message}")
        assert result.tool_message is not None
        assert "two passionate scientists" in result.tool_message
        assert len(result.content) > 1

        context = await kernel.run(chat_function, input_str="who are Emily and David?")
        print(f"Answer using input string: '{context}'")
        assert context.objects["results"][0].tool_message is not None
        assert "two passionate scientists" in context.objects["results"][0].tool_message
        assert len(context.result) > 1

        await memory_store.delete_collection(collection)
    except:
        await memory_store.delete_collection(collection)
        raise
