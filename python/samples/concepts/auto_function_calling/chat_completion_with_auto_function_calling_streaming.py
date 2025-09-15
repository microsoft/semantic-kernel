# Copyright (c) Microsoft. All rights reserved.

import asyncio

from samples.concepts.setup.chat_completion_services import Services, get_chat_completion_service_and_request_settings
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents import ChatHistory
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.core_plugins.math_plugin import MathPlugin
from semantic_kernel.core_plugins.time_plugin import TimePlugin
from semantic_kernel.functions import KernelArguments

#####################################################################
# This sample demonstrates how to build a conversational chatbot    #
# using Semantic Kernel, featuring auto function calling,           #
# streaming responses, and support for math and time plugins.       #
# The chatbot is designed to interact with the user, call functions #
# as needed, and return responses.                                  #
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

# Configure the function choice behavior. Here, we set it to Auto.
request_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

kernel.add_service(chat_completion_service)

# Pass the request settings to the kernel arguments.
arguments = KernelArguments(settings=request_settings)

# Create a chat history to store the system message, initial messages, and the conversation.
history = ChatHistory()
history.add_system_message(system_message)
history.add_user_message("Hi there, who are you?")
history.add_assistant_message("I am Mosscap, a chat bot. I'm trying to figure out what people need.")


async def main() -> None:
    print(
        "Welcome to the chat bot!\n"
        "  Type 'exit' to exit.\n"
        "  Try a math question to see function calling in action (e.g. 'what is 3+3?')."
    )

    while True:
        try:
            user_input = input("User:> ")
        except (KeyboardInterrupt, EOFError):
            print("\n\nExiting chat...")
            break

        if user_input.lower().strip() == "exit":
            print("\n\nExiting chat...")
            break

        arguments["user_input"] = user_input
        arguments["chat_history"] = history

        # Directly handle streaming of the assistant's response here
        print("Mosscap:> ", end="", flush=True)

        streamed_response_chunks: list[StreamingChatMessageContent] = []

        async for message in kernel.invoke_stream(
            chat_function,
            return_function_results=False,
            arguments=arguments,
        ):
            msg = message[0]

            # We only expect assistant messages here.
            if not isinstance(msg, StreamingChatMessageContent) or msg.role != AuthorRole.ASSISTANT:
                continue

            streamed_response_chunks.append(msg)
            print(str(msg), end="", flush=True)

        print("\n", flush=True)

        if streamed_response_chunks:
            result = "".join([str(content) for content in streamed_response_chunks])
            history.add_user_message(user_input)
            history.add_assistant_message(result)


if __name__ == "__main__":
    asyncio.run(main())
