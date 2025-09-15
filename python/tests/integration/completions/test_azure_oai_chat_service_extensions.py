# Copyright (c) Microsoft. All rights reserved.

import os
import time
from random import randint

import numpy as np
import pytest
import pytest_asyncio
from azure.identity import AzureCliCredential

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    ApiKeyAuthentication,
    AzureAISearchDataSource,
    AzureAISearchDataSourceParameters,
    DataSourceFieldsMapping,
    ExtraBody,
)
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
from semantic_kernel.memory.memory_record import MemoryRecord
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

try:
    from semantic_kernel.connectors.memory_stores.azure_cognitive_search.azure_cognitive_search_memory_store import (
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


@pytest_asyncio.fixture
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
    except Exception as e:
        await memory_store.delete_collection(collection)
        raise e


@pytest_asyncio.fixture
async def create_with_data_chat_function(kernel: Kernel, create_memory_store):
    collection, memory_store = create_memory_store
    try:
        # Load Azure OpenAI with data settings
        search_endpoint = os.getenv("AZURE_COGNITIVE_SEARCH_ENDPOINT")
        search_api_key = os.getenv("AZURE_COGNITIVE_SEARCH_ADMIN_KEY")

        extra = ExtraBody(
            data_sources=[
                AzureAISearchDataSource(
                    parameters=AzureAISearchDataSourceParameters(
                        index_name=collection,
                        endpoint=search_endpoint,
                        authentication=ApiKeyAuthentication(key=search_api_key),
                        query_type="simple",
                        fields_mapping=DataSourceFieldsMapping(
                            title_field="Description",
                            content_fields=["Text"],
                        ),
                        top_n_documents=1,
                    ),
                )
            ]
        )
        chat_service = AzureChatCompletion(service_id="chat-gpt-extensions", credential=AzureCliCredential())
        kernel.add_service(chat_service)

        prompt = "{{$chat_history}}{{$input}}"

        exec_settings = PromptExecutionSettings(
            service_id="chat-gpt-extensions",
            extension_data={"max_tokens": 2000, "temperature": 0.7, "top_p": 0.8, "extra_body": extra},
        )

        prompt_template_config = PromptTemplateConfig(
            template=prompt, description="Chat", execution_settings=exec_settings
        )

        # Create the semantic function
        kernel.add_function(function_name="chat", plugin_name="plugin", prompt_template_config=prompt_template_config)
        chat_function = kernel.get_function("plugin", "chat")
        return chat_function, kernel, collection, memory_store
    except Exception as e:
        await memory_store.delete_collection(collection)
        raise e


@pytestmark
async def test_azure_e2e_chat_completion_with_extensions(create_with_data_chat_function):
    # Create an index and populate it with some data
    chat_function, kernel, collection, memory_store = create_with_data_chat_function

    chat_history = ChatHistory()
    chat_history.add_user_message("A story about Emily and David...")
    arguments = KernelArguments(input="who are Emily and David?", chat_history=chat_history)

    # TODO: get streaming working for this test
    use_streaming = False

    try:
        result: StreamingChatMessageContent = None
        if use_streaming:
            async for message in kernel.invoke_stream(chat_function, arguments):
                result = message[0] if not result else result + message[0]
                print(message, end="")

            print(f"Answer using input string: '{result}'")
            for item in result.items:
                if isinstance(item, FunctionResultContent):
                    print(f"Content: {item.result}")
                    assert "two passionate scientists" in item.result
        else:
            result = await kernel.invoke(chat_function, arguments)
            print(f"Answer using input string: '{result}'")

        await memory_store.delete_collection(collection)
    except Exception as e:
        await memory_store.delete_collection(collection)
        raise e
