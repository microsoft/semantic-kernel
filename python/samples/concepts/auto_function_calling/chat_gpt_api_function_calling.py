# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
from functools import reduce
from typing import TYPE_CHECKING

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import (
    FunctionChoiceBehavior,
)
from semantic_kernel.connectors.ai.open_ai import (
    OpenAIChatCompletion,
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.contents import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.streaming_chat_message_content import (
    StreamingChatMessageContent,
)
from semantic_kernel.core_plugins.math_plugin import MathPlugin
from semantic_kernel.core_plugins.time_plugin import TimePlugin
from semantic_kernel.functions import KernelArguments

if TYPE_CHECKING:
    from semantic_kernel.functions import KernelFunction


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

# This concept example shows how to handle both streaming and non-streaming responses
# To toggle the behavior, set the following flag accordingly:
stream = True

kernel = Kernel()

# Note: the underlying gpt-35/gpt-4 model version needs to be at least version 0613 to support tools.
kernel.add_service(OpenAIChatCompletion(service_id="chat"))

plugins_directory = os.path.join(__file__, "../../../../../prompt_template_samples/")
# adding plugins to the kernel
kernel.add_plugin(MathPlugin(), plugin_name="math")
kernel.add_plugin(TimePlugin(), plugin_name="time")

chat_function = kernel.add_function(
    prompt="{{$chat_history}}{{$user_input}}",
    plugin_name="ChatBot",
    function_name="Chat",
)

# Enabling or disabling function calling is done by setting the `function_choice_behavior` attribute for the
# prompt execution settings. When the function_call parameter is set to "auto" the model will decide which
# function to use, if any.
#
# There are two ways to define the `function_choice_behavior` parameter:
# 1. Using the type string as `"auto"`, `"required"`, or `"none"`. For example:
#   configure `function_choice_behavior="auto"` parameter directly in the execution settings.
# 2. Using the FunctionChoiceBehavior class. For example:
#   `function_choice_behavior=FunctionChoiceBehavior.Auto()`.
# Both of these configure the `auto` tool_choice and all of the available plugins/functions
# registered on the kernel. If you want to limit the available plugins/functions, you must
# configure the `filters` dictionary attribute for each type of function choice behavior.
# For example:
#
# from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior

# function_choice_behavior = FunctionChoiceBehavior.Auto(
#     filters={"included_functions": ["time-date", "time-time", "math-Add"]}
# )
#
# The filters attribute allows you to specify either: `included_functions`, `excluded_functions`,
#  `included_plugins`, or `excluded_plugins`.

# Note: the number of responses for auto invoking tool calls is limited to 1.
# If configured to be greater than one, this value will be overridden to 1.
execution_settings = OpenAIChatPromptExecutionSettings(
    service_id="chat",
    max_tokens=2000,
    temperature=0.7,
    top_p=0.8,
    function_choice_behavior=FunctionChoiceBehavior.Auto(auto_invoke=True),
    function_choice_behavior="auto",
)

history = ChatHistory()

history.add_system_message(system_message)
history.add_user_message("Hi there, who are you?")
history.add_assistant_message(
    "I am Mosscap, a chat bot. I'm trying to figure out what people need."
)

arguments = KernelArguments(settings=execution_settings)


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
    if len(formatted_tool_calls) > 0:
        print("Tool calls:\n" + "\n\n".join(formatted_tool_calls))
    else:
        print("The model used its own knowledge and didn't return any tool calls.")


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
    result_content = []
    async for message in response:
        if (
            not execution_settings.function_choice_behavior.auto_invoke_kernel_functions
            and isinstance(message[0], StreamingChatMessageContent)
        ):
            streamed_chunks.append(message[0])
        else:
            result_content.append(message[0])
            print(str(message[0]), end="")

    if streamed_chunks:
        streaming_chat_message = reduce(
            lambda first, second: first + second, streamed_chunks
        )
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

    if stream:
        result = await handle_streaming(kernel, chat_function, arguments=arguments)
    else:
        result = await kernel.invoke(chat_function, arguments=arguments)

        # If tools are used, and auto invoke tool calls is False, the response will be of type
        # ChatMessageContent with information about the tool calls, which need to be sent
        # back to the model to get the final response.
        function_calls = [
            item
            for item in result.value[-1].items
            if isinstance(item, FunctionCallContent)
        ]
        if (
            not execution_settings.function_choice_behavior.auto_invoke_kernel_functions
            and len(function_calls) > 0
        ):
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
