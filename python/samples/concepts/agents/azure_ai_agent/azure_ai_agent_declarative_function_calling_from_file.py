# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
from typing import Annotated

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AgentRegistry, AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread
from semantic_kernel.functions.kernel_function_decorator import kernel_function

"""
The following sample demonstrates how to create an Azure AI agent that answers
user questions. The sample shows how to load a declarative spec from a file. 
The plugins/functions must already exist in the kernel.
They are not created declaratively via the spec.
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


async def main():
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        try:
            # Define the YAML file path for the sample
            file_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
                "resources",
                "declarative_spec",
                "spec.yaml",
            )

            # Create the AzureAI Agent from the YAML spec
            agent: AzureAIAgent = await AgentRegistry.create_from_file(
                file_path,
                plugins=[MenuPlugin()],
                client=client,
                settings=AzureAIAgentSettings(),  # The Spec's ChatModelId & Endpoint come from .env/env vars
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
