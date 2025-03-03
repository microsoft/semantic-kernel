# Copyright (c) Microsoft. All rights reserved.

import asyncio
import tempfile

from samples.concepts.setup.chat_completion_services import Services, get_chat_completion_service_and_request_settings
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents import ChatHistory
from semantic_kernel.core_plugins.math_plugin import MathPlugin
from semantic_kernel.core_plugins.time_plugin import TimePlugin
from semantic_kernel.functions import KernelArguments

"""
This sample demonstrates how to build a conversational chatbot
using Semantic Kernel, it features auto function calling,
but with file-based serialization of the chat history.
This sample stores and reads the chat history at every turn.
This is not the best way to do it, but clearly demonstrates the mechanics.
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

# Configure the function choice behavior. Here, we set it to Auto, where auto_invoke=True by default.
# With `auto_invoke=True`, the model will automatically choose and call functions as needed.
request_settings.function_choice_behavior = FunctionChoiceBehavior.Auto(filters={"excluded_plugins": ["ChatBot"]})

kernel.add_service(chat_completion_service)

# Pass the request settings to the kernel arguments.
arguments = KernelArguments(settings=request_settings)


async def chat(file) -> bool:
    """
    Continuously prompt the user for input and show the assistant's response.
    Type 'exit' to exit.
    """
    try:
        # Try to load the chat history from a file.
        history = ChatHistory.load_chat_history_from_file(file_path=file)
        print(f"Chat history successfully loaded {len(history.messages)} messages.")
    except Exception:
        # Create a chat history to store the system message, initial messages, and the conversation.
        print("Chat history file not found. Starting a new conversation.")
        history = ChatHistory()
        history.add_system_message(system_message)
        history.add_user_message("Hi there, who are you?")
        history.add_assistant_message("I am Mosscap, a chat bot. I'm trying to figure out what people need.")

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
    result = await kernel.invoke(chat_function, arguments=arguments)  # type: ignore

    # Update the chat history with the user's input and the assistant's response
    if result:
        print(f"Mosscap:> {result}")
        history.add_user_message(user_input)
        history.add_message(result.value[0])  # Capture the full context of the response

    # Save the chat history to a file.
    print(f"Saving {len(history.messages)} messages to the file.")
    history.store_chat_history_to_file(file_path=file)
    return True


async def main() -> None:
    chatting = True
    with tempfile.NamedTemporaryFile(mode="w+", dir=".", suffix=".json", delete=True) as file:
        print(
            "Welcome to the chat bot!\n"
            "  Type 'exit' to exit.\n"
            "  Try a math question to see function calling in action (e.g. 'what is 3+3?')."
            f"  Your chat history will be saved in: {file.name}"
        )
        while chatting:
            chatting = await chat(file.name)


if __name__ == "__main__":
    asyncio.run(main())
