# Copyright (c) Microsoft. All rights reserved.


import asyncio
import os
from functools import reduce
from typing import TYPE_CHECKING

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAIChatPromptExecutionSettings
from semantic_kernel.contents import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.core_plugins import MathPlugin, TimePlugin
from semantic_kernel.filters.auto_function_invocation.auto_function_invocation_context import (
    AutoFunctionInvocationContext,
)
from semantic_kernel.filters.filter_types import FilterTypes
from semantic_kernel.functions import KernelArguments

if TYPE_CHECKING:
    from semantic_kernel.functions import KernelFunction

##################################################################
# Sample Notes:

# In this sample, we're showing how to configure a yaml config file with `function_choice_behavior` settings.
# The `function_choice_behavior` settings are used to control the auto function calling behavior of the model.
# The related config is located in the `resources` folder under the title `function_choice_yaml/ChatBot`.

# The execution settings look like:

# execution_settings:
#   chat:
#     function_choice_behavior:
#       type: auto
#       maximum_auto_invoke_attempts: 5
#       functions:
#         - time.date
#         - time.time
#         - math.Add

# This is another way of configuring the function choice behavior for the model like:
# FunctionChoiceBehavior.Auto(filters={"included_functions": ["time.date", "time.time", "math.Add"]})

# The `maximum_auto_invoke_attempts` attribute is used to control the number of times the model will attempt to call a
# function. If wanting to disable auto function calling, set this attribute to 0 or configure the
# `auto_invoke_kernel_functions` attribute to False.
##################################################################

system_message = """
You are a chat bot. Your name is Mosscap and
you have one goal: figure out what people need.
Your full name, should you need to know it, is
Splendid Speckled Mosscap. You communicate
effectively, but you tend to answer with long
flowery prose. You are also a math wizard,
especially for adding and subtracting.
You also excel at joke telling, where your tone is often sarcastic.
Once you have the answer I am looking for,
you will return a full answer to me as soon as possible.
"""

kernel = Kernel()

# Note: the underlying gpt-35/gpt-4 model version needs to be at least version 0613 to support tools.
service_id = "chat"
kernel.add_service(OpenAIChatCompletion(service_id=service_id))

# adding plugins to the kernel
kernel.add_plugin(MathPlugin(), plugin_name="math")
kernel.add_plugin(TimePlugin(), plugin_name="time")

chat_function = kernel.add_function(
    prompt="{{$chat_history}}{{$user_input}}",
    plugin_name="ChatBot",
    function_name="Chat",
)

plugin_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
    "resources",
)
chat_plugin = kernel.add_plugin(plugin_name="function_choice_yaml", parent_directory=plugin_path)

history = ChatHistory()

history.add_system_message(system_message)
history.add_user_message("Hi there, who are you?")
history.add_assistant_message("I am Mosscap, a chat bot. I'm trying to figure out what people need.")


# To control auto function calling you can do it two ways:
# 1. Configure the attribute `auto_invoke_kernel_functions` as False
# 2. Configure the `maximum_auto_invoke_attempts` as 0.
# These can be done directly on the FunctionChoiceBehavior.Auto/Required/None object or via the JSON/yaml config.
execution_settings: OpenAIChatPromptExecutionSettings = chat_plugin["ChatBot"].prompt_execution_settings[service_id]

arguments = KernelArguments()


# We will hook up a filter to show which function is being called.
# A filter is a piece of custom code that runs at certain points in the process
# this sample has a filter that is called during Auto Function Invocation
# this filter will be called for each function call in the response.
# You can name the function itself with arbitrary names, but the signature needs to be:
# `context, next`
# You are then free to run code before the call to the next filter or the function itself.
# if you want to terminate the function calling sequence. set context.terminate to True
@kernel.filter(FilterTypes.AUTO_FUNCTION_INVOCATION)
async def auto_function_invocation_filter(context: AutoFunctionInvocationContext, next):
    """A filter that will be called for each function call in the response."""
    print("\nAuto function invocation filter")
    print(f"Function: {context.function.fully_qualified_name}")

    # if we don't call next, it will skip this function, and go to the next one
    await next(context)


def print_tool_calls(message: ChatMessageContent) -> None:
    # A helper method to pretty print the tool calls from the message.
    # This is only triggered if auto invoke tool calls is disabled.
    items = message.items
    formatted_tool_calls = []
    for i, item in enumerate(items, start=1):
        if isinstance(item, FunctionCallContent):
            tool_call_id = item.id
            function_name = item.name
            function_arguments = item.arguments
            formatted_str = (
                f"tool_call {i} id: {tool_call_id}\n"
                f"tool_call {i} function name: {function_name}\n"
                f"tool_call {i} arguments: {function_arguments}"
            )
            formatted_tool_calls.append(formatted_str)
    print("Tool calls:\n" + "\n\n".join(formatted_tool_calls))


async def handle_streaming(
    kernel: Kernel,
    chat_function: "KernelFunction",
    arguments: KernelArguments,
) -> str | None:
    response = kernel.invoke_stream(
        chat_function,
        return_function_results=False,
        arguments=arguments,
    )

    print("Mosscap:> ", end="")
    streamed_chunks: list[StreamingChatMessageContent] = []
    result_content: list[StreamingChatMessageContent] = []
    async for message in response:
        if (
            not execution_settings.function_choice_behavior.auto_invoke_kernel_functions
            and isinstance(message[0], StreamingChatMessageContent)
            and message[0].role == AuthorRole.ASSISTANT
        ):
            streamed_chunks.append(message[0])
        elif isinstance(message[0], StreamingChatMessageContent) and message[0].role == AuthorRole.ASSISTANT:
            result_content.append(message[0])
            print(str(message[0]), end="")

    if streamed_chunks:
        streaming_chat_message = reduce(lambda first, second: first + second, streamed_chunks)
        if hasattr(streaming_chat_message, "content"):
            print(streaming_chat_message.content)
        print("Auto tool calls is disabled, printing returned tool calls...")
        print_tool_calls(streaming_chat_message)

    print("\n")
    if result_content:
        return "".join([str(content) for content in result_content])
    return None


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

    stream = False
    if stream:
        result = await handle_streaming(kernel, chat_function, arguments=arguments)
    else:
        result = await kernel.invoke(chat_plugin["ChatBot"], arguments=arguments)

        # If tools are used, and auto invoke tool calls is False, the response will be of type
        # ChatMessageContent with information about the tool calls, which need to be sent
        # back to the model to get the final response.
        function_calls = [item for item in result.value[-1].items if isinstance(item, FunctionCallContent)]
        if len(function_calls) > 0:
            print_tool_calls(result.value[0])
            return True

        print(f"Mosscap:> {result}")

    history.add_user_message(user_input)
    history.add_assistant_message(str(result))
    return True


async def main() -> None:
    chatting = True
    print(
        "Welcome to the chat bot!\
        \n  Type 'exit' to exit.\
        \n  Try a math question to see the function calling in action (i.e. what is 3+3?)."
    )
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
