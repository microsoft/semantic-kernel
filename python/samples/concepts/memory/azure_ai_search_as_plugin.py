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
from semantic_kernel.contents import ChatHistory
from semantic_kernel.data import (
    SearchOptions,
    VectorSearchFilter,
    VectorSearchOptions,
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordUtils,
    VectorStoreRecordVectorField,
    vectorstoremodel,
)
from semantic_kernel.filters.filter_types import FilterTypes
from semantic_kernel.filters.functions.function_invocation_context import FunctionInvocationContext
from semantic_kernel.functions import (
    KernelArguments,
    KernelParameterMetadata,
)


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
azure_ai_search_collection: AzureAISearchCollection[HotelSampleClassType] = AzureAISearchCollection(
    collection_name="hotels-sample-index", data_model_type=HotelSampleClass
)


def update_options_search(options: SearchOptions, func_args: dict[str, Any]) -> SearchOptions:
    for key, value in func_args.items():
        if key == "city":
            if options.filter:
                options.filter.equal_to("address/city", value)
            else:
                options.filter = VectorSearchFilter.equal_to("address/city", value)
    return options


def update_options_details(options: SearchOptions, func_args: dict[str, Any]) -> SearchOptions:
    for key, value in func_args.items():
        if key == "hotel_id":
            if options.filter:
                options.filter.equal_to("hotel_id", value)
            else:
                options.filter = VectorSearchFilter.equal_to("hotel_id", value)
    return options


plugin = kernel.add_functions(
    plugin_name="azure_ai_search",
    functions=[
        azure_ai_search_collection.create_kernel_function(
            search_function="vectorizable_text_search",
            description="A hotel search engine, allows searching for hotels in specific cities, "
            "you do not have to specify that you are searching for hotels, for all, use `*`.",
            options=VectorSearchOptions(
                filter=VectorSearchFilter.equal_to("address/country", "USA"),
                select_fields=[
                    "hotel_id",
                    "description",
                    "description_fr",
                    "address",
                    "tags",
                    "rating",
                    "category",
                    "location",
                    "rooms",
                ],
            ),
            parameters=[
                KernelParameterMetadata(
                    name="query", description="What to search for.", type="str", is_required=True, type_object=str
                ),
                KernelParameterMetadata(
                    name="city",
                    description="The city that you want to search for a hotel in.",
                    type="str",
                    is_required=False,
                    type_object=str,
                ),
                KernelParameterMetadata(
                    name="count",
                    description="Number of results to return.",
                    type="int",
                    is_required=False,
                    default_value=2,
                    type_object=int,
                ),
            ],
            update_options_function=update_options_search,
        ),
        azure_ai_search_collection.create_kernel_function(
            search_function="vectorizable_text_search",
            function_name="get_details",
            description="Get details about a hotel, by ID, use the overview function to get the ID.",
            options=VectorSearchOptions(
                query="*",
                count=1,
            ),
            parameters=[
                KernelParameterMetadata(
                    name="hotel_id",
                    description="The hotel ID to get details for.",
                    type="str",
                    is_required=True,
                    type_object=str,
                )
            ],
            update_options_function=update_options_details,
        ),
    ],
)


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
    function_choice_behavior=FunctionChoiceBehavior.Auto(filters={"excluded_plugins": ["ChatBot"]}),
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
        print(f"Calling Azure AI Search ({context.function.name}) with arguments:")
        for arg in context.arguments:
            if arg in ("user_input", "chat_history"):
                continue
            print(f'  {arg}: "{context.arguments[arg]}"')
        await next(context)
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
    arguments["country"] = "USA"
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
        \n  Try to find a hotel to your liking!."
    )
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
