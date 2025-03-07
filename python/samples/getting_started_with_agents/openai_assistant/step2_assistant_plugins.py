# Copyright (c) Microsoft. All rights reserved.
import asyncio
from typing import Annotated

from semantic_kernel.agents.open_ai import AzureAssistantAgent
from semantic_kernel.functions import kernel_function

"""
The following sample demonstrates how to create an OpenAI         
assistant using either Azure OpenAI or OpenAI. The sample
shows how to use a Semantic Kernel plugin as part of the
OpenAI Assistant.  
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
    "What is the special drink?",
    "How much is it?",
    "Thank you",
]


async def main():
    # 1. Create the client using Azure OpenAI resources and configuration
    client, model = AzureAssistantAgent.setup_resources()

    # 2. Create the assistant on the Azure OpenAI service
    definition = await client.beta.assistants.create(
        model=model,
        instructions="Answer questions about the menu.",
        name="Host",
    )

    # 3. Create a Semantic Kernel agent for the Azure OpenAI assistant
    agent = AzureAssistantAgent(
        client=client,
        definition=definition,
        plugins=[MenuPlugin()],  # The plugins can be passed in as a list to the constructor
    )
    # Note: plugins can also be configured on the Kernel and passed in as a parameter to the OpenAIAssistantAgent

    # 4. Create a new thread on the Azure OpenAI assistant service
    thread = await agent.client.beta.threads.create()

    try:
        for user_input in USER_INPUTS:
            # 5. Add the user input to the chat thread
            await agent.add_chat_message(
                thread_id=thread.id,
                message=user_input,
            )
            print(f"# User: '{user_input}'")
            # 6. Invoke the agent for the current thread and print the response
            async for content in agent.invoke(thread_id=thread.id):
                print(f"# Agent: {content.content}")
    finally:
        # 7. Clean up the resources
        await agent.client.beta.threads.delete(thread.id)
        await agent.client.beta.assistants.delete(assistant_id=agent.id)

    """
    You should see output similar to the following:

    # User: 'Hello'
    # Agent: Hello! How can I assist you today?
    # User: 'What is the special soup?'
    # Agent: The special soup today is Clam Chowder. Would you like to know more about any other menu items?
    # User: 'What is the special drink?'
    # Agent: The special drink today is Chai Tea. Would you like more information on anything else?
    # User: 'Thank you'
    # Agent: You're welcome! If you have any more questions or need further assistance, feel free to ask. 
        Enjoy your day!
     """


if __name__ == "__main__":
    asyncio.run(main())
