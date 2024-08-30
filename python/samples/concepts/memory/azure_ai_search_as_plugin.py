# Copyright (c) Microsoft. All rights reserved.


import asyncio
from collections.abc import Coroutine
from typing import Annotated, Any, TypeVar

from pydantic import BaseModel

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import (
    OpenAIChatCompletion,
    OpenAIChatPromptExecutionSettings,
    OpenAIEmbeddingPromptExecutionSettings,
    OpenAITextEmbedding,
)
from semantic_kernel.connectors.memory.azure_ai_search import AzureAISearchCollection
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.data import (
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordUtils,
    VectorStoreRecordVectorField,
    vectorstoremodel,
)
from semantic_kernel.filters.filter_types import FilterTypes
from semantic_kernel.filters.functions.function_invocation_context import FunctionInvocationContext
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.search.filter_clause import FilterClause
from semantic_kernel.search.text_search_options import TextSearchOptions


@vectorstoremodel
class HotelSampleClass(BaseModel):
    hotel_id: Annotated[str, VectorStoreRecordKeyField]
    hotel_name: Annotated[str | None, VectorStoreRecordDataField()] = None
    description: Annotated[
        str,
        VectorStoreRecordDataField(
            has_embedding=True, embedding_property_name="description_vector", is_full_text_searchable=True
        ),
    ]
    description_vector: Annotated[
        list[float] | None,
        VectorStoreRecordVectorField(
            dimensions=1536,
            local_embedding=True,
            embedding_settings={"embedding": OpenAIEmbeddingPromptExecutionSettings(dimensions=1536)},
        ),
    ] = None
    description_fr: Annotated[
        str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="description_fr_vector")
    ]
    description_fr_vector: Annotated[
        list[float] | None,
        VectorStoreRecordVectorField(
            dimensions=1536,
            local_embedding=True,
            embedding_settings={"embedding": OpenAIEmbeddingPromptExecutionSettings(dimensions=1536)},
        ),
    ] = None
    category: Annotated[str, VectorStoreRecordDataField()]
    tags: Annotated[list[str], VectorStoreRecordDataField()]
    parking_included: Annotated[bool | None, VectorStoreRecordDataField()] = None
    last_renovation_date: Annotated[str | None, VectorStoreRecordDataField()] = None
    rating: Annotated[float, VectorStoreRecordDataField()]
    location: Annotated[dict[str, Any], VectorStoreRecordDataField()]
    address: Annotated[dict[str, str | None], VectorStoreRecordDataField()]
    rooms: Annotated[list[dict[str, Any]], VectorStoreRecordDataField()]


HotelSampleClassType = TypeVar("HotelSampleClassType", bound=HotelSampleClass)

kernel = Kernel()
service_id = "chat"
kernel.add_service(OpenAIChatCompletion(service_id=service_id))
embeddings = OpenAITextEmbedding(service_id="embedding", ai_model_id="text-embedding-3-small")
kernel.add_service(embeddings)
vectorizer = VectorStoreRecordUtils(kernel)
store = AzureAISearchCollection[HotelSampleClassType](
    collection_name="hotels-sample-index", data_model_type=HotelSampleClass
)
options = TextSearchOptions(
    search_filters=[FilterClause(field_name="site", value="devblogs.microsoft.com", clause_type="equality")],
    count=4,
)
plugin = store.create_plugin_from_search(
    plugin_name="azure_ai_search",
    map_function=lambda x: f"{x.hotel_id}, {x.description}, {x.address}, {x.tags}",
)
kernel.add_plugin(plugin)
chat_function = kernel.add_function(
    prompt="{{$chat_history}}{{$user_input}}",
    plugin_name="ChatBot",
    function_name="Chat",
)
execution_settings = OpenAIChatPromptExecutionSettings(
    service_id="chat",
    max_tokens=2000,
    temperature=0.7,
    top_p=0.8,
    function_choice_behavior=FunctionChoiceBehavior.Auto(auto_invoke=True),
)

history = ChatHistory()
system_message = """
You are a chat bot. Your name is Mosscap and
you have one goal: help people find a hotel.
Your full name, should you need to know it, is
Splendid Speckled Mosscap. You communicate
effectively, but you tend to answer with long
flowery prose.
"""
history.add_system_message(system_message)
history.add_user_message("Hi there, who are you?")
history.add_assistant_message("I am Mosscap, a chat bot. I'm trying to figure out what people need.")

arguments = KernelArguments(settings=execution_settings)


@kernel.filter(filter_type=FilterTypes.FUNCTION_INVOCATION)
async def log_search_filter(context: FunctionInvocationContext, next: Coroutine[FunctionInvocationContext, Any, None]):
    if context.function.plugin_name == "azure_ai_search":
        print("Calling Azure AI Search with arguments:")
        if "query" in context.arguments:
            print(f'  Query: "{context.arguments["query"]}"')
        if "count" in context.arguments:
            print(f'  Count: "{context.arguments["count"]}"')
        if "skip" in context.arguments:
            print(f'  Skip: "{context.arguments["skip"]}"')
        await next(context)
        print("Azure AI Search completed.")
        print("  raw results:")
        print(f"    {context.result}")
    else:
        await next(context)


async def chat() -> bool:
    try:
        user_input = input("User:> ")
    except KeyboardInterrupt:
        print("\n\nExiting chat...")
        return False
    except EOFError:
        print("\n\nExiting chat...")
        return False

    if user_input == "exit":
        print("\n\nExiting chat...")
        return False
    arguments["user_input"] = user_input
    arguments["chat_history"] = history
    result = await kernel.invoke(chat_function, arguments=arguments)
    print(f"Mosscap:> {result}")
    history.add_user_message(user_input)
    history.add_assistant_message(str(result))
    return True


async def main():
    chatting = True
    print(
        "Welcome to the chat bot!\
        \n  Type 'exit' to exit.\
        \n  Try a math question to see the function calling in action (i.e. what is 3+3?)."
    )
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
