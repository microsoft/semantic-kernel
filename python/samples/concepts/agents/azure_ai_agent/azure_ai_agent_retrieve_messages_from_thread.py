# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Annotated

from azure.identity.aio import AzureCliCredential

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread
from semantic_kernel.functions import kernel_function

"""
The following sample demonstrates how to create an Azure AI agent that answers
questions about a sample menu using a Semantic Kernel Plugin. After all questions
are answered, it retrieves and prints the messages from the thread.
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
    "How much does that cost?",
    "Thank you",
]


async def main() -> None:
    async with (
        AzureCliCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. Create an agent on the Azure AI agent service
        agent_definition = await client.agents.create_agent(
            model=AzureAIAgentSettings().model_deployment_name,
            name="Host",
            instructions="Answer questions about the menu.",
        )

        # 2. Create a Semantic Kernel agent for the Azure AI agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
            plugins=[MenuPlugin()],  # Add the plugin to the agent
        )

        # 3. Create a thread for the agent
        # If no thread is provided, a new thread will be
        # created and returned with the initial response
        thread: AzureAIAgentThread | None = None

        try:
            for user_input in USER_INPUTS:
                print(f"# User: {user_input}")
                # 4. Invoke the agent for the specified thread for response
                async for response in agent.invoke(
                    messages=user_input,
                    thread=thread,
                ):
                    print(f"# {response.name}: {response}")
                    thread = response.thread
        finally:
            # 5. Cleanup: Delete the thread and agent
            # await thread.delete() if thread else None
            await client.agents.delete_agent(agent.id)

        print("*" * 50)
        print("# Messages in the thread (asc order):\n")
        async for msg in thread.get_messages(sort_order="asc"):
            print(f"# {msg.role} for name={msg.name}: {msg.content}")
        print("*" * 50)

        await thread.delete() if thread else None

        """
        # User: Hello
        # Host: Hello! How can I assist you with the menu today?
        # User: What is the special soup?
        # Host: The special soup today is Clam Chowder. Would you like to know more about it or anything else 
            on the menu?
        # User: How much does that cost?
        # Host: The Clam Chowder costs $9.99. Would you like to order it or need information on other items?
        # User: Thank you
        # Host: You're welcome! If you have any more questions or need assistance with the menu, feel free to ask. 
            Enjoy your meal!
        **************************************************
        # Messages in the thread (asc order):

        # AuthorRole.USER for name=asst_mXwZOwyJLxXGtaYKHizRH6Ip: Hello
        # AuthorRole.ASSISTANT for name=asst_mXwZOwyJLxXGtaYKHizRH6Ip: Hello! How can I assist you with the menu today?
        # AuthorRole.USER for name=asst_mXwZOwyJLxXGtaYKHizRH6Ip: What is the special soup?
        # AuthorRole.ASSISTANT for name=asst_mXwZOwyJLxXGtaYKHizRH6Ip: The special soup today is Clam Chowder. Would 
            you like to know more about it or anything else on the menu?
        # AuthorRole.USER for name=asst_mXwZOwyJLxXGtaYKHizRH6Ip: How much does that cost?
        # AuthorRole.ASSISTANT for name=asst_mXwZOwyJLxXGtaYKHizRH6Ip: The Clam Chowder costs $9.99. Would you like to 
            order it or need information on other items?
        # AuthorRole.USER for name=asst_mXwZOwyJLxXGtaYKHizRH6Ip: Thank you
        # AuthorRole.ASSISTANT for name=asst_mXwZOwyJLxXGtaYKHizRH6Ip: You're welcome! If you have any more questions 
            or need assistance with the menu, feel free to ask. Enjoy your meal!
        """


if __name__ == "__main__":
    asyncio.run(main())
