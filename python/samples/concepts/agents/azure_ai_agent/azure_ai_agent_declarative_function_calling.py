# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Annotated

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AgentRegistry, AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel

"""
The following sample demonstrates how to create an Azure AI agent that answers
user questions. This sample demonstrates the basic steps to create an agent
and simulate a conversation with the agent.

The interaction with the agent is via the `get_response` method, which sends a
user input to the agent and receives a response from the agent. The conversation
history is maintained by the agent service, i.e. the responses are automatically
associated with the thread. Therefore, client code does not need to maintain the
conversation history.
"""


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


# Function spec

spec = """ 
type: foundry_agent
name: FunctionCallingAgent
description: This agent uses the provided functions to answer questions about the menu.
instructions: Use the provided functions to answer questions about the menu.
model:
  id: ${AzureAI:ChatModelId}
  connection:
    connection_string: ${AzureAI:ConnectionString}
  options:
    temperature: 0.4
tools:
  - id: MenuPlugin.get_specials
    type: function
    description: Get the specials from the menu.
    options:
      parameters:
        type: object
        properties: {}
  - id: MenuPlugin.get_item_price
    type: function
    description: Get the price of an item on the menu.
    options:
      parameters:
        type: object
        properties:
          menu_item:
            type: string
            description: The name of the menu item.
        required: ["menu_item"]
"""

settings = AzureAIAgentSettings()  # The Spec's ChatModelId & ConnectionString come from .env/env vars


async def main():
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        try:
            # Define an instance of the kernel
            # The kernel must be supplied to be able to resolve the plugins
            kernel = Kernel()
            kernel.add_plugin(MenuPlugin(), "MenuPlugin")

            # Create the AzureAI Agent from the YAML spec
            agent: AzureAIAgent = await AgentRegistry.create_from_yaml(
                spec,
                kernel=kernel,
                client=client,
                settings=settings,
            )

            # Create the agent
            user_inputs = [
                "Hello",
                "What is the special soup?",
                "How much does that cost?",
                "Thank you",
            ]

            # Create a thread for the agent
            # If no thread is provided, a new thread will be
            # created and returned with the initial response
            thread: AzureAIAgentThread | None = None

            for user_input in user_inputs:
                print(f"# User: '{user_input}'")
                # Invoke the agent for the specified task
                async for response in agent.invoke(
                    messages=user_input,
                    thread=thread,
                ):
                    print(f"# {response.name}: {response}")
                    # Store the thread for the next iteration
                    thread = response.thread
        finally:
            # Cleanup: Delete the thread and agent
            await client.agents.delete_agent(agent.id) if agent else None
            await thread.delete() if thread else None


if __name__ == "__main__":
    asyncio.run(main())
