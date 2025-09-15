# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import TYPE_CHECKING

from samples.concepts.setup.chat_completion_services import Services, get_chat_completion_service_and_request_settings
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.core_plugins.math_plugin import MathPlugin
from semantic_kernel.core_plugins.time_plugin import TimePlugin
from semantic_kernel.functions import KernelArguments

if TYPE_CHECKING:
    pass

#####################################################################
# This sample demonstrates how to build a conversational chatbot    #
# using Semantic Kernel, featuring manual function calling,         #
# non-streaming responses, and support for math and time plugins.   #
# The chatbot is designed to interact with the user, call functions #
# as needed, and return responses. With auto function calling       #
# disabled, the tool calls will be printed to the console.          #
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

# You can select from the following chat completion services that support function calling:
# - Services.OPENAI
# - Services.AZURE_OPENAI
# - Services.AZURE_AI_INFERENCE
# - Services.ANTHROPIC
# - Services.BEDROCK
# - Services.GOOGLE_AI
# - Services.MISTRAL_AI
# - Services.OLLAMA
# - Services.ONNX
# - Services.VERTEX_AI
# - Services.DEEPSEEK
# Please make sure you have configured your environment correctly for the selected chat completion service.
chat_completion_service, request_settings = get_chat_completion_service_and_request_settings(Services.AZURE_OPENAI)

# Configure the function choice behavior. Here, we set it to Auto, where auto_invoke=False.
# With `FunctionChoiceBehavior(auto_invoke=False)`, the model may return tool call instructions
# that you must handle and call manually. We will only print the tool calls in this sample.
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


async def chat() -> bool:
    """
    Continuously prompt the user for input and show the assistant's response.
    Type 'exit' to exit.
    """
    try:
        user_input = input("User:> ")
    except (KeyboardInterrupt, EOFError):
        print("\n\nExiting chat...")
        return False

    if user_input.lower().strip() == "exit":
        print("\n\nExiting chat...")
        return False

    arguments["user_input"] = user_input
    arguments["chat_history"] = history

    # Handle non-streaming responses
    result = await kernel.invoke(chat_function, arguments=arguments)

    # If function calls are returned, we show them on the console.
    if result and result.value:
        # Extract function calls from the returned content
        function_calls = [item for item in result.value[-1].items if isinstance(item, FunctionCallContent)]
        if len(function_calls) > 0:
            print_tool_calls(result.value[0])
            # At this point, you'd handle these calls manually if desired.
            # For now, we just print them.
            return True

    # If no function calls to handle, just print the assistant's response
    if result:
        print(f"Mosscap:> {result}")

    # Update the chat history with the user's input and the assistant's response
    if result:
        history.add_user_message(user_input)
        history.add_assistant_message(str(result))

    return True


async def main() -> None:
    print(
        "Welcome to the chat bot!\n"
        "  Type 'exit' to exit.\n"
        "  Try a math question to see function calling in action (e.g. 'what is 3+3?')."
    )
    chatting = True
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
