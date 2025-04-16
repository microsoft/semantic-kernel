# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
from pathlib import Path

from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.mcp import MCPStdioPlugin
from semantic_kernel.core_plugins.time_plugin import TimePlugin

"""
The following sample demonstrates how to create a chat completion agent that
answers questions about Github using a Semantic Kernel Plugin from a MCP server. 

It uses the Azure OpenAI service to create a agent, so make sure to 
set the required environment variables for the Azure AI Foundry service:
- AZURE_OPENAI_CHAT_DEPLOYMENT_NAME
- Optionally: AZURE_OPENAI_API_KEY 
If this is not set, it will try to use DefaultAzureCredential.

"""


async def main():
    # 1. Create the agent
    async with (
        MCPStdioPlugin(
            name="Menu",
            description="Menu plugin, for details about the menu, call this plugin.",
            command="uv",
            args=[
                f"--directory={str(Path(os.path.dirname(__file__)).joinpath('servers'))}",
                "run",
                "menu_agent_server.py",
            ],
            env={
                "AZURE_OPENAI_CHAT_DEPLOYMENT_NAME": os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
                "AZURE_OPENAI_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT"),
            },
        ) as restaurant_agent,
        MCPStdioPlugin(
            name="Booking",
            description="Restaurant Booking Plugin",
            command="uv",
            args=[
                f"--directory={str(Path(os.path.dirname(__file__)).joinpath('servers'))}",
                "run",
                "restaurant_booking_agent_server.py",
            ],
            env={
                "AZURE_OPENAI_CHAT_DEPLOYMENT_NAME": os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
                "AZURE_OPENAI_ENDPOINT": os.getenv("AZURE_OPENAI_ENDPOINT"),
            },
        ) as booking_agent,
    ):
        agent = ChatCompletionAgent(
            service=AzureChatCompletion(),
            name="PersonalAssistant",
            instructions="Help the user with restaurant bookings.",
            plugins=[restaurant_agent, booking_agent, TimePlugin()],
        )

        # 2. Create a thread to hold the conversation
        # If no thread is provided, a new thread will be
        # created and returned with the initial response
        thread: ChatHistoryAgentThread | None = None
        while True:
            user_input = input("User: ")
            if user_input.lower() == "exit":
                break
            # 3. Invoke the agent for a response
            response = await agent.get_response(messages=user_input, thread=thread)
            print(f"# {response.name}: {response} ")
            thread = response.thread

        # 4. Cleanup: Clear the thread
        await thread.delete() if thread else None


if __name__ == "__main__":
    asyncio.run(main())
