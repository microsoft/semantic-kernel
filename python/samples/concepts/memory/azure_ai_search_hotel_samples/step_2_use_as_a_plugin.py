# Copyright (c) Microsoft. All rights reserved.


import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from step_0_data_model import HotelSampleClass

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import (
    OpenAIChatCompletion,
    OpenAIChatPromptExecutionSettings,
    OpenAITextEmbedding,
)
from semantic_kernel.connectors.memory.azure_ai_search import AzureAISearchCollection
from semantic_kernel.contents import ChatHistory

###
# The data model used for this sample is based on the hotel data model from the Azure AI Search samples.
# When deploying a new index in Azure AI Search using the import wizard you can choose to deploy the 'hotel-samples'
# dataset, see here: https://learn.microsoft.com/en-us/azure/search/search-get-started-portal.
# This is the dataset used in this sample with some modifications.
# This model adds vectors for the 2 descriptions in English and French.
# Both are based on the 1536 dimensions of the OpenAI models.
# You can adjust this at creation time and then make the change below as well.
# This sample assumes the index is deployed, and the vectors have been filled.
# Use the step_1_interact_with_the_collection.py sample, with `first_run = True` to fill the vectors.
###
from semantic_kernel.data import (
    VectorSearchFilter,
    VectorSearchOptions,
)
from semantic_kernel.data.text_search import SearchOptions
from semantic_kernel.filters import FilterTypes, FunctionInvocationContext
from semantic_kernel.functions import (
    KernelArguments,
    KernelParameterMetadata,
)

# Note: you may need to update this `collection_name` depending upon how your index is named.
COLLECTION_NAME = "hotels-sample-index"

# Create Kernel and add both chat completion and text embeddings services.
kernel = Kernel()
service_id = "chat"
kernel.add_service(OpenAIChatCompletion(service_id=service_id))
embeddings = OpenAITextEmbedding(service_id="embedding", ai_model_id="text-embedding-3-small")
kernel.add_service(embeddings)

# Create a Text Search object, with a Azure AI Search collection.
# using the `from_vector_text_search` method means that this plugin will only use text search.
# You can also choose to use the `from_vectorized_search` method to use vector search.
# Or the `from_vectorizable_text_search` method if the collection is setup to vectorize incoming texts.
collection = AzureAISearchCollection[str, HotelSampleClass](
    collection_name=COLLECTION_NAME, data_model_type=HotelSampleClass
)
text_search = collection.create_text_search_from_vector_text_search()


# Before we create the plugin, we want to create a function that will help the plugin work the way we want it to.
# This function allows us to create the plugin with a parameter called `city` that
# then get's put into a filter for address/city.
# This function has to adhere to the `OptionsUpdateFunctionType` signature.
# which consists of 3 named arguments, `query`, `options`, and `parameters`.
# and kwargs.
# It returns a tuple of the query and options.
# The default version that is used when not supplying this, reads the parameters and if there is
# a parameter that is not `query`, `top`, or 'skip`, and it can find a value for it, either in the kwargs
# or the default value specified in the parameter, it will add a filter to the options.
# In this case, we are adding a filter to the options to filter by the city, but since the technical name
# of that field in the index is `address/city`, want to do this manually.
# this can also be used to replace a complex technical name in your index with a friendly name towards the LLM.
def update_options_search(
    query: str, options: SearchOptions, parameters: list[Any] | None = None, **kwargs: Any
) -> tuple[Any, SearchOptions]:
    if "city" in kwargs:
        options.filter.equal_to("address/city", kwargs["city"])
    return query, options


# Next we create the plugin, with two functions.
# When you only need one function, you can use the `KernelPlugin.from_text_search_with_search` (and similar) methods.
# Those create a plugin you can then add to the kernel.
plugin = kernel.add_functions(
    plugin_name="azure_ai_search",
    functions=[
        text_search.create_search(
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
            # Next to the dynamic filters based on parameters, I can specify options that are always used.
            # this can include the `top` and `skip` parameters, but also filters that are always applied.
            # In this case, I am filtering by country, so only hotels in the USA are returned.
            options=VectorSearchOptions(
                filter=VectorSearchFilter.equal_to("address/country", "USA"),
            ),
            parameters=[
                KernelParameterMetadata(
                    name="query", description="What to search for.", type="str", is_required=True, type_object=str
                ),
                KernelParameterMetadata(
                    name="city",
                    description="The city that you want to search for a hotel in.",
                    type="str",
                    type_object=str,
                ),
                KernelParameterMetadata(
                    name="top",
                    description="Number of results to return.",
                    type="int",
                    default_value=2,
                    type_object=int,
                ),
            ],
            # and here the above created function is passed in.
            options_update_function=update_options_search,
        ),
        text_search.create_search(
            # This second function is a more detailed one, that uses a `hotel_id` to get details about a hotel.
            # we set the top to 1, so that only 1 record is returned.
            function_name="get_details",
            description="Get details about a hotel, by ID, use the overview function to get the ID.",
            options=VectorSearchOptions(
                top=1,
            ),
            parameters=[
                KernelParameterMetadata(
                    name="hotel_id",
                    description="The hotel ID to get details for.",
                    type="str",
                    is_required=True,
                    type_object=str,
                ),
                KernelParameterMetadata(
                    name="hotel_name",
                    description="The name of the hotel.",
                    type="str",
                    type_object=str,
                    is_required=True,
                ),
            ],
            # it uses the default update options that will turn the hotel_id into a filter.
        ),
    ],
)

# Now we create the chat function, that will use the OpenAI chat service.
chat_function = kernel.add_function(
    prompt="{{$chat_history}}{{$user_input}}",
    plugin_name="ChatBot",
    function_name="Chat",
)
# we set the function choice to Auto, so that the LLM can choose the correct function to call.
# and we exclude the ChatBot plugin, so that it does not call itself.
# this means that it has access to 2 functions, that were defined above.
execution_settings = OpenAIChatPromptExecutionSettings(
    function_choice_behavior=FunctionChoiceBehavior.Auto(filters={"excluded_plugins": ["ChatBot"]}),
    service_id="chat",
    max_tokens=2000,
    temperature=0.7,
    top_p=0.8,
)

history = ChatHistory()
system_message = """
You are a chat bot. Your name is Mosscap and
you have one goal: help people find a hotel.
Your full name, should you need to know it, is
Splendid Speckled Mosscap. You communicate
effectively, but you tend to answer with long
flowery prose. You always make sure to include the
hotel_id in your answers so that the user can
use it to get more information.
"""
history.add_system_message(system_message)
history.add_user_message("Hi there, who are you?")
history.add_assistant_message("I am Mosscap, a chat bot. I'm trying to figure out what people need.")

arguments = KernelArguments(settings=execution_settings)


# This filter will log all calls to the Azure AI Search plugin.
# This allows us to see what parameters are being passed to the plugin.
# And this gives us a way to debug the search experience and if necessary tweak the parameters and descriptions.
@kernel.filter(filter_type=FilterTypes.FUNCTION_INVOCATION)
async def log_search_filter(
    context: FunctionInvocationContext, next: Callable[[FunctionInvocationContext], Awaitable[None]]
):
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
