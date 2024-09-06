# Copyright (c) Microsoft. All rights reserved.


import asyncio
from collections.abc import Callable, Coroutine, Sequence
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
from semantic_kernel.data.const import DEFAULT_DESCRIPTION
from semantic_kernel.data.filters.vector_search_filter import VectorSearchFilter
from semantic_kernel.data.search_options_base import SearchOptions
from semantic_kernel.data.text_search import TextSearch
from semantic_kernel.data.vector_search_options import VectorSearchOptions
from semantic_kernel.filters.filter_types import FilterTypes
from semantic_kernel.filters.functions.function_invocation_context import FunctionInvocationContext
from semantic_kernel.functions import kernel_function
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata


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
store: AzureAISearchCollection[HotelSampleClassType] = AzureAISearchCollection(
    collection_name="hotels-sample-index", data_model_type=HotelSampleClass
)


def create_kernel_function(
    service: TextSearch,
    search_function: str,
    options: SearchOptions | None,
    parameters: list[KernelParameterMetadata] | None = None,
    return_parameter: KernelParameterMetadata | None = None,
    function_name: str = "search",
    description: str = DEFAULT_DESCRIPTION,
    map_function: Callable[[Any], str] | None = None,
) -> KernelFunction:
    """Create a function from a search service.

    Args:
        search_function: The search function.
        options: The search options.
        parameters: The parameters for the function.
        return_parameter: The return parameter for the function.
        function_name: The name of the function.
        description: The description of the function.
        map_function: The function to map the search results to strings.

    """
    search_func = service._search_function_map.get(search_function)
    if not search_func:
        raise ValueError(f"Search function '{search_function}' not found.")

    @kernel_function(name=function_name, description=description)
    async def search_wrapper(**kwargs: Any) -> Sequence[str]:
        results = await search_func(options=service._create_options(options, **kwargs))
        return service._map_result_to_strings(results, map_function)

    return KernelFunctionFromMethod(
        method=search_wrapper,
        parameters=parameters or service._default_parameter_metadata(),
        return_parameter=return_parameter or service._default_return_parameter_metadata(),
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
        store.create_kernel_function(
            search_function="get_search_result",
            description="A hotel search engine, allows searching for hotels in specific cities, "
            "you do not have to specify that you are searching for hotels, for all, use `*`.",
            options=VectorSearchOptions(
                filter=VectorSearchFilter.equal_to("address/country", "USA"),
                select_fields=["hotel_id", "description", "address", "tags", "rating", "category"],
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
        store.create_kernel_function(
            search_function="get_search_result",
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

#             # "dynamic_filters": [
#             #     DynamicFilterClause(field_name="address/city", parameter_name="city", clause_type="equality"),
#             #     DynamicFilterClause(
#             #         field_name="address/country",
#             #         parameter_name="country",
#             #         clause_type="direct",
#             #         function=lambda x: f"address/country eq '{x}'",
#             #     ),
#             # ],


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
        \n  Try a math question to see the function calling in action (i.e. what is 3+3?)."
    )
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
