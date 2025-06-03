# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Awaitable, Callable

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAIChatPromptExecutionSettings
from semantic_kernel.connectors.search.brave import BraveSearch
from semantic_kernel.contents import ChatHistory
from semantic_kernel.filters import FilterTypes, FunctionInvocationContext
from semantic_kernel.functions import KernelArguments, KernelParameterMetadata, KernelPlugin

"""
This project demonstrates how to integrate the Brave Search API as a plugin into the Semantic Kernel 
framework to enable conversational AI capabilities with real-time web information. 

To use Brave Search, you need an API key, which can be obtained by login to
https://api-dashboard.search.brave.com/ and creating a subscription key.
After that store it under the name `BRAVE_API_KEY` in a .env file or your environment variables.
"""

kernel = Kernel()
kernel.add_service(OpenAIChatCompletion(service_id="chat"))
kernel.add_plugin(
    KernelPlugin.from_text_search_with_search(
        BraveSearch(),
        plugin_name="brave",
        description="Get details about Semantic Kernel concepts.",
        parameters=[
            KernelParameterMetadata(
                name="query",
                description="The search query.",
                type="str",
                is_required=True,
                type_object=str,
            ),
            KernelParameterMetadata(
                name="top",
                description="The number of results to return.",
                type="int",
                is_required=False,
                default_value=2,
                type_object=int,
            ),
            KernelParameterMetadata(
                name="skip",
                description="The number of results to skip.",
                type="int",
                is_required=False,
                default_value=0,
                type_object=int,
            ),
        ],
    )
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
    function_choice_behavior=FunctionChoiceBehavior.Auto(auto_invoke=True),
)

history = ChatHistory()
system_message = """
You are a chat bot, specialized in Semantic Kernel, Microsoft LLM orchestration SDK.
Assume questions are related to that, and use the Brave search plugin to find answers.
"""
history.add_system_message(system_message)
history.add_user_message("Hi there, who are you?")
history.add_assistant_message("I am Mosscap, a chat bot. I'm trying to figure out what people need.")

arguments = KernelArguments(settings=execution_settings)


@kernel.filter(filter_type=FilterTypes.FUNCTION_INVOCATION)
async def log_brave_filter(
    context: FunctionInvocationContext, next: Callable[[FunctionInvocationContext], Awaitable[None]]
):
    if context.function.plugin_name == "brave":
        print("Calling Brave search with arguments:")
        if "query" in context.arguments:
            print(f'  Query: "{context.arguments["query"]}"')
        if "count" in context.arguments:
            print(f'  Count: "{context.arguments["count"]}"')
        if "skip" in context.arguments:
            print(f'  Skip: "{context.arguments["skip"]}"')
        await next(context)
        print("Brave search completed.")
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
        \n  Try to find out more about the inner workings of Semantic Kernel."
    )
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
