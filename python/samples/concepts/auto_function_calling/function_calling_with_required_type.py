# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
from functools import reduce
from typing import TYPE_CHECKING

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior, FunctionChoiceType
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAIChatPromptExecutionSettings
from semantic_kernel.contents import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.core_plugins import MathPlugin, TimePlugin
from semantic_kernel.functions import KernelArguments

if TYPE_CHECKING:
    from semantic_kernel.functions import KernelFunction


# In this sample, we're working with the `FunctionChoiceBehavior.Required` type for auto function calling.
# This type mandates that the model calls a specific function or a set of functions to handle the user input.
# By default, the `maximum_auto_invoke_attempts` is set to 1. This can be adjusted by setting this attribute
# in the `FunctionChoiceBehavior.Required` class.
#
# Note that if the maximum auto invoke attempts exceed the number of functions the model calls, it may repeat calling a
# function and ultimately return a tool call response. For example, if we specify required plugins as `math-Multiply`
# and `math-Add`, and set the maximum auto invoke attempts to 5, and query `What is 3+4*5?`, the model will first call
# the `math-Multiply` function, then the `math-Add` function, satisfying 2 of the 5 max auto invoke attempts.
# The remaining 3 attempts will continue calling `math-Add` because the execution settings are still configured with a
# tool_choice `required` and the supplied tools. The final result will be a tool call response.
#
# This behavior is true for both streaming and non-streaming responses.

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
Start all your answers with the current time.
"""

# This concept example shows how to handle both streaming and non-streaming responses
# To toggle the behavior, set the following flag accordingly:
stream = False

kernel = Kernel()

# Note: the underlying gpt-35/gpt-4 model version needs to be at least version 0613 to support tools.
service_id = "chat"
kernel.add_service(OpenAIChatCompletion(service_id=service_id))

plugins_directory = os.path.join(__file__, "../../../../../prompt_template_samples/")
# adding plugins to the kernel
kernel.add_plugin(MathPlugin(), plugin_name="math")
kernel.add_plugin(TimePlugin(), plugin_name="time")

chat_function = kernel.add_function(
    prompt="{{$chat_history}}{{$user_input}}",
    plugin_name="ChatBot",
    function_name="Chat",
)

# enabling or disabling function calling is done by setting the function_choice_behavior parameter for the
# prompt execution settings. When the function_call parameter is set to "required" the model will decide which
# function to use, if any. If you only want to use a specific function, configure the filters dict with either:
# 'excluded_plugins', 'included_plugins', 'excluded_functions', or 'included_functions'. For example, the
# format for that is 'PluginName-FunctionName', (i.e. 'math-Add').
# if the model or api version does not support this you will get an error.

# Note: by default, the number of responses for auto invoking `required` tool calls is limited to 1.
# The value may be configured to be more than one depending upon your scenario.
execution_settings = OpenAIChatPromptExecutionSettings(
    service_id=service_id,
    max_tokens=2000,
    temperature=0.7,
    top_p=0.8,
    function_choice_behavior=FunctionChoiceBehavior.Required(
        auto_invoke=False,
        filters={"included_functions": ["time-time", "time-date"]},
    ),
)

history = ChatHistory()

history.add_system_message(system_message)
history.add_user_message("Hi there, who are you?")
history.add_assistant_message("I am Mosscap, a chat bot. I'm trying to figure out what people need.")

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
) -> None:
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
            (
                not execution_settings.function_choice_behavior.auto_invoke_kernel_functions
                or execution_settings.function_choice_behavior.type_ == FunctionChoiceType.REQUIRED
            )
            and isinstance(message[0], StreamingChatMessageContent)
            and message[0].role == AuthorRole.ASSISTANT
        ):
            streamed_chunks.append(message[0])
        elif isinstance(message[0], StreamingChatMessageContent) and message[0].role == AuthorRole.ASSISTANT:
            result_content.append(message[0])
            print(str(message[0]), end="")

    if streamed_chunks:
        streaming_chat_message = reduce(lambda first, second: first + second, streamed_chunks)
        if hasattr(streaming_chat_message, "content") and streaming_chat_message.content:
            print(streaming_chat_message.content)
        print("Printing returned tool calls...")
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
        function_calls = [item for item in result.value[-1].items if isinstance(item, FunctionCallContent)]
        if not execution_settings.function_choice_behavior.auto_invoke_kernel_functions and len(function_calls) > 0:
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
        \n  Try a question to see the function calling in action (i.e. what is the current time?)."
    )
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
