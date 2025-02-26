# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Annotated

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents.azure_ai import AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.contents import AuthorRole
from semantic_kernel.functions import kernel_function

"""
The following sample demonstrates how to create an Azure AI agent that answers
questions about a sample menu using a Semantic Kernel Plugin.
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
    ai_agent_settings = AzureAIAgentSettings.create()

    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. Create an agent on the Azure AI agent service
        agent_definition = await client.agents.create_agent(
            model=ai_agent_settings.model_deployment_name,
            name="Host",
            instructions="Answer questions about the menu.",
        )

        # 2. Create a Semantic Kernel agent for the Azure AI agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
            # Optionally configure polling options
            # polling_options=RunPollingOptions(run_polling_interval=timedelta(seconds=1)),
        )

        # 3. Add a plugin to the agent via the kernel
        agent.kernel.add_plugin(MenuPlugin(), plugin_name="menu")

        # 4. Create a new thread on the Azure AI agent service
        thread = await client.agents.create_thread()

        try:
            for user_input in USER_INPUTS:
                # 5. Add the user input as a chat message
                await agent.add_chat_message(thread_id=thread.id, message=user_input)
                print(f"# User: {user_input}")
                # 6. Invoke the agent for the specified thread for response
                async for content in agent.invoke(
                    thread_id=thread.id,
                    temperature=0.2,  # override the agent-level temperature setting with a run-time value
                ):
                    if content.role != AuthorRole.TOOL:
                        print(f"# Agent: {content.content}")
        finally:
            # 7. Cleanup: Delete the thread and agent
            await client.agents.delete_thread(thread.id)
            await client.agents.delete_agent(agent.id)

        """
        Sample Output:
        # User: Hello
        # Agent: Hello! How can I assist you today?
        # User: What is the special soup?
        # ...
        """


if __name__ == "__main__":
    asyncio.run(main())
