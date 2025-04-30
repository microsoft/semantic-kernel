# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import os

from samples.concepts.setup.chat_completion_services import Services, get_chat_completion_service_and_request_settings
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.mcp import MCPStdioPlugin
from semantic_kernel.contents import ChatHistory
from semantic_kernel.utils.logging import setup_logging

"""
This sample demonstrates how to build a conversational chatbot
using Semantic Kernel, 
it creates a Plugin from a MCP server config and adds it to the kernel.
The chatbot is designed to interact with the user, call MCP tools 
as needed, and return responses.

To run this sample, make sure to run:
`pip install semantic-kernel[mcp]`

or install the mcp package manually.

In addition, different MCP Stdio servers need different commands to run.
For example, the Github plugin requires `npx`, others use `uvx` or `docker`.

Make sure those are available in your PATH.
"""

# System message defining the behavior and persona of the chat bot.
system_message = """
You are a chat bot. And you help users interact with Github.
You are especially good at answering questions about the Microsoft semantic-kernel project.
You can call functions to get the information you need.
"""

setup_logging()
logging.getLogger("semantic_kernel.connectors.mcp").setLevel(logging.DEBUG)

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
    # Create a plugin from the MCP server config and add it to the kernel.
    # The MCP server plugin is defined using the MCPStdioPlugin class.
    # The command and args are specific to the MCP server you want to run.
    # For example, the Github MCP Server uses `npx` to run the server.
    # There is also a MCPSsePlugin, which takes a URL.
    async with MCPStdioPlugin(
        name="Github",
        description="Github Plugin",
        command="docker",
        args=["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "ghcr.io/github/github-mcp-server"],
        env={"GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")},
    ) as github_plugin:
        # instead of using this async context manager, you can also use:
        # await github_plugin.connect()
        # and then await github_plugin.close() at the end of the program.

        # Add the plugin to the kernel.
        kernel.add_plugin(github_plugin)

        # Start the chat loop.
        print("Welcome to the chat bot!\n  Type 'exit' to exit.\n")
        chatting = True
        while chatting:
            chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
