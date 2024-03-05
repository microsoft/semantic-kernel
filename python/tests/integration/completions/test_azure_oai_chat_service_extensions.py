# Copyright (c) Microsoft. All rights reserved.

import os
import time
from random import randint

import numpy as np
import pytest

import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureAISearchDataSources,
    AzureDataSources,
    ExtraBody,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

try:
    from semantic_kernel.connectors.memory.azure_cognitive_search.azure_cognitive_search_memory_store import (
        AzureCognitiveSearchMemoryStore,
    )

    azure_ai_search_installed = True

except ImportError:
    azure_ai_search_installed = False

if os.environ.get("AZURE_COGNITIVE_SEARCH_ENDPOINT") and os.environ.get("AZURE_COGNITIVE_SEARCH_ADMIN_KEY"):
    azure_ai_search_settings = True
else:
    azure_ai_search_settings = False

pytestmark = pytest.mark.skipif(
    not (azure_ai_search_installed and azure_ai_search_settings),
    reason="Azure AI Search is not installed",
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
            service_id="chat-gpt-extensions",
            deployment_name=deployment_name,
            api_key=api_key,
            endpoint=endpoint,
            api_version="2023-12-01-preview",
            use_extensions=True,
        )
        kernel.add_service(chat_service)

        prompt = "{{$input}}"

        exec_settings = PromptExecutionSettings(
            service_id="chat-gpt-extensions",
            extension_data={"max_tokens": 2000, "temperature": 0.7, "top_p": 0.8, "extra_body": extra},
        )

        prompt_template_config = PromptTemplateConfig(
            template=prompt, description="Write a short story.", execution_settings=exec_settings
        )

        # Create the semantic function
        chat_function = kernel.create_function_from_prompt(
            function_name="story", plugin_name="plugin", prompt_template_config=prompt_template_config
        )

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

    arguments = KernelArguments(input="who are Emily and David?")

    # TODO: get streaming working for this test
    use_streaming = False

    try:
        result = None
        if use_streaming:
            async for message in kernel.invoke_stream(chat_function, arguments):
                result = message[0] if not result else result + message[0]
                print(message, end="")

            print(f"Answer using input string: '{result}'")
            print(f"Tool message: {result.tool_message}")
            assert result.tool_message is not None
            assert "two passionate scientists" in result.tool_message
            assert len(result.content) > 1
        else:
            result = await kernel.invoke(chat_function, arguments)
            print(f"Answer using input string: '{result}'")

        await memory_store.delete_collection(collection)
    except:
        await memory_store.delete_collection(collection)
        raise
