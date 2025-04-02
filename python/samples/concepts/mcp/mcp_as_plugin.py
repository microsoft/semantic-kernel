# Copyright (c) Microsoft. All rights reserved.

import asyncio

from samples.concepts.setup.chat_completion_services import Services, get_chat_completion_service_and_request_settings
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.mcp import mcp_server_as_plugin
from semantic_kernel.contents import ChatHistory

"""
This sample demonstrates how to build a conversational chatbot
using Semantic Kernel, 
it creates a Plugin from a MCP server config and adds it to the kernel.
The chatbot is designed to interact with the user, call MCP tools 
as needed, and return responses.
"""

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
chat_service, settings = get_chat_completion_service_and_request_settings(Services.OPENAI)

# Configure the function choice behavior. Here, we set it to Auto, where auto_invoke=True by default.
# With `auto_invoke=True`, the model will automatically choose and call functions as needed.
settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

kernel.add_service(chat_service)

# Create a chat history to store the system message, initial messages, and the conversation.
history = ChatHistory()
history.add_system_message(system_message)


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

    history.add_user_message(user_input)
    result = await chat_service.get_chat_message_content(history, settings, kernel=kernel)
    if result:
        print(f"Mosscap:> {result}")
        history.add_message(result)

    return True


async def main() -> None:
    # Make sure to have NPX installed and available in your PATH.
    # Find the NPX executable in the system PATH.
    # github_plugin, _ = await create_plugin_from_mcp_server(
    #     plugin_name="GitHub",
    #     description="Github Plugin",
    #     command="npx",
    #     args=["-y", "@modelcontextprotocol/server-github"],
    # )
    async with mcp_server_as_plugin(
        plugin_name="Github",
        description="Github Plugin",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-github"],
    ) as github_plugin:
        kernel.add_plugin(github_plugin)
        print("Welcome to the chat bot!\n  Type 'exit' to exit.\n")
        chatting = True
        while chatting:
            chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
