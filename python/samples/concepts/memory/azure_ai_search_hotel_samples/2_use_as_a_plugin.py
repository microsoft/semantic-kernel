# Copyright (c) Microsoft. All rights reserved.


import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from samples.concepts.memory.azure_ai_search_hotel_samples.data_model import (
    HotelSampleClass,
    custom_index,
    load_records,
)
from semantic_kernel.agents import AgentThread, ChatCompletionAgent
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAITextEmbedding
from semantic_kernel.connectors.azure_ai_search import AzureAISearchCollection
from semantic_kernel.filters import FilterTypes, FunctionInvocationContext
from semantic_kernel.functions import KernelParameterMetadata, KernelPlugin
from semantic_kernel.kernel_types import OptionalOneOrList

"""
This sample builds on the previous one, but can be run independently.
It uses the data model defined in step_0_data_model.py, and with that creates a collection
and creates two kernel functions from those that are then made available to a LLM.
The first function is a search function that allows you to search for hotels, optionally filtering for a city.
The second function is a details function that allows you to get details about a hotel.
"""


# Create an Azure AI Search collection.
collection = AzureAISearchCollection[str, HotelSampleClass](
    record_type=HotelSampleClass, embedding_generator=OpenAITextEmbedding()
)
# load the records
records = load_records()
# get the set of cities
cities: set[str] = set()
for record in records:
    if record.Address.Country == "USA" and record.Address.City:
        cities.add(record.Address.City)


# Before we create the plugin, we want to create a function that will help the plugin work the way we want it to.
# This function allows us to create the plugin with a parameter called `city` that
# then get's put into a filter for address/city.
# This function has to adhere to the `DynamicFilterFunction` signature.
# which consists of 2 named arguments, `filter`, and `parameters`.
# and kwargs.
# It returns the updated filter.
# The default version that is used when not supplying this, reads the parameters and if there is
# a parameter that is not `query`, `top`, or 'skip`, and it can find a value for it, either in the kwargs
# or the default value specified in the parameter, it will add a filter to the options.
# In this case, we are adding a filter to the options to filter by the city, but since the technical name
# of that field in the index is `address/city`, want to do this manually.
# this can also be used to replace a complex technical name in your index with a friendly name towards the LLM.
def filter_update(
    filter: OptionalOneOrList[Callable | str] | None = None,
    parameters: list["KernelParameterMetadata"] | None = None,
    **kwargs: Any,
) -> OptionalOneOrList[Callable | str] | None:
    if "city" in kwargs:
        city = kwargs["city"]
        if city not in cities:
            raise ValueError(f"City '{city}' is not in the list of cities: {', '.join(cities)}")
        # we need the actual value and not a named param, otherwise the parser will not be able to find it.
        new_filter = f"lambda x: x.Address.City == '{city}'"
        if filter is None:
            filter = new_filter
        elif isinstance(filter, list):
            filter.append(new_filter)
        else:
            filter = [filter, new_filter]
    return filter


# Next we create the Agent, with two functions.
travel_agent = ChatCompletionAgent(
    name="TravelAgent",
    description="A travel agent that helps you find a hotel.",
    service=OpenAIChatCompletion(),
    instructions="""You are a travel agent. Your name is Mosscap and
you have one goal: help people find a hotel.
Your full name, should you need to know it, is
Splendid Speckled Mosscap. You communicate
effectively, but you tend to answer with long
flowery prose. You always make sure to include the
hotel_id in your answers so that the user can
use it to get more information.""",
    function_choice_behavior=FunctionChoiceBehavior.Auto(),
    plugins=[
        KernelPlugin(
            name="azure_ai_search",
            description="A plugin that allows you to search for hotels in Azure AI Search.",
            functions=[
                collection.create_search_function(
                    # this create search method uses the `search` method of the text search object.
                    # remember that the text_search object for this sample is based on
                    # the text_search method of the Azure AI Search.
                    # but it can also be used with the other vector search methods.
                    # This method's description, name and parameters are what will be serialized as part of the tool
                    # call functionality of the LLM.
                    # And crafting these should be part of the prompt design process.
                    # The default parameters are `query`, `top`, and `skip`, but you specify your own.
                    # The default parameters match the parameters of the VectorSearchOptions class.
                    description="A hotel search engine, allows searching for hotels in specific cities, "
                    "you do not have to specify that you are searching for hotels, for all, use `*`.",
                    search_type="keyword_hybrid",
                    # Next to the dynamic filters based on parameters, I can specify options that are always used.
                    # this can include the `top` and `skip` parameters, but also filters that are always applied.
                    # In this case, I am filtering by country, so only hotels in the USA are returned.
                    filter=lambda x: x.Address.Country == "USA",
                    parameters=[
                        KernelParameterMetadata(
                            name="query",
                            description="What to search for.",
                            type="str",
                            is_required=True,
                            type_object=str,
                        ),
                        KernelParameterMetadata(
                            name="city",
                            description="The city that you want to search for a hotel "
                            f"in, values are: {', '.join(cities)}",
                            type="str",
                            type_object=str,
                        ),
                        KernelParameterMetadata(
                            name="top",
                            description="Number of results to return.",
                            type="int",
                            default_value=5,
                            type_object=int,
                        ),
                    ],
                    # and here the above created function is passed in.
                    filter_update_function=filter_update,
                    # finally, we specify the `string_mapper` function that is used to convert the record to a string.
                    # This is used to make sure the relevant information from the record is passed to the LLM.
                    string_mapper=lambda x: f"(hotel_id :{x.record.HotelId}) {x.record.HotelName} (rating {x.record.Rating}) - {x.record.Description}. Address: {x.record.Address.StreetAddress}, {x.record.Address.City}, {x.record.Address.StateProvince}, {x.record.Address.Country}. Number of room types: {len(x.record.Rooms)}. Last renovated: {x.record.LastRenovationDate}.",  # noqa: E501
                ),
                collection.create_search_function(
                    # This second function is a more detailed one, that uses a `HotelId` to get details about a hotel.
                    # we set the top to 1, so that only 1 record is returned.
                    function_name="get_details",
                    description="Get details about a hotel, by ID, use the generic search function to get the ID.",
                    top=1,
                    parameters=[
                        KernelParameterMetadata(
                            name="HotelId",
                            description="The hotel ID to get details for.",
                            type="str",
                            is_required=True,
                            type_object=str,
                        ),
                    ],
                ),
            ],
        )
    ],
)


# This filter will log all calls to the Azure AI Search plugin.
# This allows us to see what parameters are being passed to the plugin.
# And this gives us a way to debug the search experience and if necessary tweak the parameters and descriptions.
@travel_agent.kernel.filter(filter_type=FilterTypes.FUNCTION_INVOCATION)
async def log_search_filter(
    context: FunctionInvocationContext, next: Callable[[FunctionInvocationContext], Awaitable[None]]
):
    print(f"Calling Azure AI Search ({context.function.name}) with arguments:")
    for arg in context.arguments:
        if arg in ("chat_history"):
            continue
        print(f'  {arg}: "{context.arguments[arg]}"')
    await next(context)


async def chat():
    # Create the Azure AI Search collection
    async with collection:
        # Check if the collection exists.
        await collection.ensure_collection_exists(index=custom_index)
        if not await collection.get(top=1):
            await collection.upsert(records)
        thread: AgentThread | None = None
        while True:
            try:
                user_input = input("User:> ")
            except KeyboardInterrupt:
                print("\n\nExiting chat...")
                break
            except EOFError:
                print("\n\nExiting chat...")
                break

            if user_input == "exit":
                print("\n\nExiting chat...")
                break

            result = await travel_agent.get_response(messages=user_input, thread=thread)
            print(f"Agent: {result.content}")
            thread = result.thread

        delete_collection = input("Do you want to delete the collection? (y/n): ")
        if delete_collection.lower() == "y":
            await collection.ensure_collection_deleted()
            print("Collection deleted.")
        else:
            print("Collection not deleted.")


async def main():
    print(
        "Welcome to the chat bot!\
        \n  Type 'exit' to exit.\
        \n  Try to find a hotel to your liking!"
    )
    await chat()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
