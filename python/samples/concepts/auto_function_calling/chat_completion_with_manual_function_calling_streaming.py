# Copyright (c) Microsoft. All rights reserved.

import asyncio
from functools import reduce
from typing import TYPE_CHECKING

from samples.concepts.setup.chat_completion_services import Services, get_chat_completion_service_and_request_settings
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.core_plugins.math_plugin import MathPlugin
from semantic_kernel.core_plugins.time_plugin import TimePlugin
from semantic_kernel.functions import KernelArguments

if TYPE_CHECKING:
    pass

#####################################################################
# This sample demonstrates how to build a conversational chatbot    #
# using Semantic Kernel, featuring dynamic function calling,        #
# streaming responses, and support for math and time plugins.       #
# The chatbot is designed to interact with the user, call functions #
# as needed, and return responses. If auto function calling is      #
# disabled, then the tool calls will be printed to the console.     #
#####################################################################

# System message defining the behavior and persona of the chat bot.
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

# Create and configure the kernel.
kernel = Kernel()

# Load some sample plugins (for demonstration of function calling).
kernel.add_plugin(MathPlugin(), plugin_name="math")
kernel.add_plugin(TimePlugin(), plugin_name="time")

# Define a chat function (a template for how to handle user input).
chat_function = kernel.add_function(
    prompt="{{$chat_history}}{{$user_input}}",
    plugin_name="ChatBot",
    function_name="Chat",
)

# Configure the chat completion service and request settings.
chat_completion_service, request_settings = get_chat_completion_service_and_request_settings(Services.AZURE_OPENAI)

# Configure the function choice behavior to Auto with auto_invoke=False.
# This means the model may return tool calls that must be manually handled.
request_settings.function_choice_behavior = FunctionChoiceBehavior.Auto(auto_invoke=False)
kernel.add_service(chat_completion_service)

# Pass the request settings to the kernel arguments.
arguments = KernelArguments(settings=request_settings)

# Create a chat history to store the system message, initial messages, and the conversation.
history = ChatHistory()
history.add_system_message(system_message)
history.add_user_message("Hi there, who are you?")
history.add_assistant_message("I am Mosscap, a chat bot. I'm trying to figure out what people need.")


def print_tool_calls(message: ChatMessageContent) -> None:
    """
    A helper function to pretty print the tool calls found in a ChatMessageContent message.
    This is useful when auto tool invocation is disabled and the model returns calls that you must handle.
    """
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
        print("\n[Tool calls returned by the model]:\n" + "\n\n".join(formatted_tool_calls))
    else:
        print("\n[No tool calls returned by the model]")


async def main() -> None:
    print(
        "Welcome to the chat bot!\n"
        "  Type 'exit' to exit.\n"
        "  Try a math question to see function calling in action (e.g. 'what is 3+3?')."
    )

    while True:
        # Get user input
        try:
            user_input = input("User:> ")
        except (KeyboardInterrupt, EOFError):
            print("\n\nExiting chat...")
            break

        if user_input.lower().strip() == "exit":
            print("\n\nExiting chat...")
            break

        # Prepare arguments for the model invocation
        arguments["user_input"] = user_input
        arguments["chat_history"] = history

        print("Mosscap:> ", end="", flush=True)

        # Lists to store streamed chunks
        streamed_tool_chunks: list[StreamingChatMessageContent] = []
        streamed_response_chunks: list[StreamingChatMessageContent] = []

        async for message in kernel.invoke_stream(
            chat_function,
            return_function_results=False,
            arguments=arguments,
        ):
            msg = message[0]

            # Expecting assistant messages only
            if not isinstance(msg, StreamingChatMessageContent) or msg.role != AuthorRole.ASSISTANT:
                continue

            # If auto_invoking is False, the model may send tool calls in separate chunks.
            if hasattr(msg, "function_invoke_attempt"):
                # This chunk is part of a tool call instruction
                streamed_tool_chunks.append(msg)
            else:
                # Normal assistant response text
                streamed_response_chunks.append(msg)
                print(str(msg), end="", flush=True)

        print("\n", flush=True)

        # If we have tool call instructions
        if streamed_tool_chunks:
            # Group streamed tool chunks by `function_invoke_attempt`
            grouped_chunks = {}
            for chunk in streamed_tool_chunks:
                key = getattr(chunk, "function_invoke_attempt", None)
                if key is not None:
                    grouped_chunks.setdefault(key, []).append(chunk)

            # Process each group of chunks
            for attempt, chunks in grouped_chunks.items():
                try:
                    combined_content = reduce(lambda first, second: first + second, chunks)
                    if hasattr(combined_content, "content"):
                        print(f"[function_invoke_attempt {attempt} content]:\n{combined_content.content}")

                    print("[Auto function calling is OFF] Here are the returned tool calls:")
                    print_tool_calls(combined_content)
                except Exception as e:
                    print(f"Error processing chunks for function_invoke_attempt {attempt}: {e}")

        # Update the chat history with user input and assistant response, if any
        if streamed_response_chunks:
            result = "".join([str(content) for content in streamed_response_chunks])
            history.add_user_message(user_input)
            history.add_assistant_message(str(result))


if __name__ == "__main__":
    asyncio.run(main())
