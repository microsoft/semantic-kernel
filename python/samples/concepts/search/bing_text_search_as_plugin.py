# Copyright (c) Microsoft. All rights reserved.


from collections.abc import Coroutine
from typing import Any

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import (
    OpenAIChatCompletion,
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.search.bing import BingSearch
from semantic_kernel.connectors.search.bing.bing_search import BingSearch
from semantic_kernel.contents import ChatHistory
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.data import TextSearchFilter, TextSearchOptions
from semantic_kernel.data.filters.text_search_filter import TextSearchFilter
from semantic_kernel.data.text_search_options import TextSearchOptions
from semantic_kernel.filters.filter_types import FilterTypes
from semantic_kernel.filters.functions.function_invocation_context import FunctionInvocationContext
from semantic_kernel.functions import KernelArguments
from semantic_kernel.functions.kernel_arguments import KernelArguments

kernel = Kernel()
service_id = "chat"
kernel.add_service(OpenAIChatCompletion(service_id=service_id))

kernel.add_functions(
    plugin_name="bing",
    functions=[
        BingSearch().create_kernel_function(
            search_function="get_text_search_results",
            description="Get details about Semantic Kernel concepts.",
            options=TextSearchOptions(
                filter=TextSearchFilter.equal_to(
                    "site", "https://github.com/microsoft/semantic-kernel/tree/main/python"
                ),
                top=6,
            ),
        )
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
    function_choice_behavior=FunctionChoiceBehavior.Auto(auto_invoke=True),
)

history = ChatHistory()
system_message = """
You are a chat bot, specialized in Semantic Kernel, Microsoft LLM orchestration SDK.
Assume questions are related to that, and use the Bing search plugin to find answers.
"""
history.add_system_message(system_message)
history.add_user_message("Hi there, who are you?")
history.add_assistant_message("I am Mosscap, a chat bot. I'm trying to figure out what people need.")

arguments = KernelArguments(settings=execution_settings)


@kernel.filter(filter_type=FilterTypes.FUNCTION_INVOCATION)
async def log_bing_filter(context: FunctionInvocationContext, next: Coroutine[FunctionInvocationContext, Any, None]):
    if context.function.plugin_name == "bing":
        print("Calling Bing search with arguments:")
        if "query" in context.arguments:
            print(f'  Query: "{context.arguments["query"]}"')
        if "count" in context.arguments:
            print(f'  Count: "{context.arguments["count"]}"')
        if "skip" in context.arguments:
            print(f'  Skip: "{context.arguments["skip"]}"')
        await next(context)
        print("Bing search completed.")
        # print("  raw results:")
        # print(f"    {context.result}")
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
