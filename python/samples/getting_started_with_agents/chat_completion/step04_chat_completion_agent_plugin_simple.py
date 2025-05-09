# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Annotated

from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import kernel_function

"""
The following sample demonstrates how to create a chat completion agent that
answers questions about a sample menu using a Semantic Kernel Plugin. The Chat
Completion Service is passed directly via the ChatCompletionAgent constructor.
Additionally, the plugin is supplied via the constructor.
"""


# Define a sample plugin for the sample
class MenuPlugin:
    """A sample Menu Plugin used for the concept sample."""

    @kernel_function(description="Provides a list of specials from the menu.")
    def get_specials(self) -> Annotated[str, "Returns the specials from the menu."]:
        return """
        Special Soup: Clam Chowder
        Special Salad: Cobb Salad
        Special Drink: Chai Tea
        """

    @kernel_function(description="Provides the price of the requested menu item.")
    def get_item_price(
        self, menu_item: Annotated[str, "The name of the menu item."]
    ) -> Annotated[str, "Returns the price of the menu item."]:
        return "$9.99"


# Simulate a conversation with the agent
USER_INPUTS = [
    "Hello",
    "What is the special soup?",
    "What does that cost?",
    "Thank you",
]


async def main():
    # 1. Create the agent
    agent = ChatCompletionAgent(
        service=AzureChatCompletion(),
        name="Host",
        instructions="Answer questions about the menu.",
        plugins=[MenuPlugin()],
    )

    # 2. Create a thread to hold the conversation
    # If no thread is provided, a new thread will be
    # created and returned with the initial response
    thread: ChatHistoryAgentThread = None

    for user_input in USER_INPUTS:
        print(f"# User: {user_input}")
        # 4. Invoke the agent for a response
        response = await agent.get_response(messages=user_input, thread=thread)
        print(f"# {response.name}: {response} ")
        thread = response.thread

    # 4. Cleanup: Clear the thread
    await thread.delete() if thread else None

    """
    Sample output:
    # User: Hello
    # Host: Hello! How can I assist you today?
    # User: What is the special soup?
    # Host: The special soup is Clam Chowder.
    # User: What does that cost?
    # Host: The special soup, Clam Chowder, costs $9.99.
    # User: Thank you
    # Host: You're welcome! If you have any more questions, feel free to ask. Enjoy your day!
    """


if __name__ == "__main__":
    asyncio.run(main())
