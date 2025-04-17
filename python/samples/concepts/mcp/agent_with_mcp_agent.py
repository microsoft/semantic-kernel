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


"""
User: what restaurants can I choose from?
# PersonalAssistant: Here are the available restaurants you can choose from:

1. **The Farm**: A classic steakhouse with a rustic atmosphere.
2. **The Harbor**: A seafood restaurant with a view of the ocean.
3. **The Joint**: A casual eatery with a diverse menu.

Let me know if you would like to make a booking or need more information about any specific restaurant! 
User: the farm sounds nice, what are the specials there?
# PersonalAssistant: The specials at The Farm are:

- **Special Entree:** T-bone steak
- **Special Salad:** Caesar Salad
- **Special Drink:** Old Fashioned

Let me know if you'd like to make a booking or if you need any more information! 
User: That entree sounds great, how much does it cost?
# PersonalAssistant: The cost of the T-bone steak at The Farm is $9.99. Would you like to proceed with a booking? 
User: yes, for 2 people tomorrow
# PersonalAssistant: I can confirm a booking for 2 people at The Farm for tomorrow, April 17, 2025. What time would you 
like the reservation? 
User: at 2000
# PersonalAssistant: I apologize, but the booking at The Farm for tomorrow at 20:00 has been denied. However, 
I was able to confirm bookings at the following restaurants:

- **The Harbor**: Booking confirmed.
- **The Joint**: Booking confirmed.

If you'd like to book at one of these restaurants or try a different time or restaurant, just let me know! 
User: try 21.00
# PersonalAssistant: Your table for 2 people at The Farm has been successfully booked for tomorrow, April 17, 2025, 
at 21:00. Enjoy your meal! If you need anything else, feel free to ask. 
User: exit
"""

if __name__ == "__main__":
    asyncio.run(main())
