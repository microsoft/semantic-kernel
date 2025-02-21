# Copyright (c) Microsoft. All rights reserved.
import asyncio
from typing import Annotated

from semantic_kernel.agents.open_ai import OpenAIAssistantAgent
from semantic_kernel.contents import AuthorRole
from semantic_kernel.functions import kernel_function

"""
The following sample demonstrates how to create an OpenAI         
assistant using either Azure OpenAI or OpenAI. OpenAI Assistants  
allow for function calling, the use of file search and a          
code interpreter. Assistant Threads are used to manage the        
conversation state, similar to a Semantic Kernel Chat History.    
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


async def main():
    # Create the OpenAI Assistant Agent
    # client = OpenAIAssistantAgent.create_openai_client()

    # To create an OpenAIAssistantAgent for Azure OpenAI, use the following:
    client = OpenAIAssistantAgent.create_azure_openai_client()

    # Create the assistant definition
    definition = await client.beta.assistants.create(
        model="gpt-4o",
        instructions="Answer questions about the menu.",
        name="Host",
        tools=[{"type": "code_interpreter"}],
    )

    # Create the OpenAIAssistantAgent instance
    agent = OpenAIAssistantAgent(
        client=client,
        definition=definition,
        plugins=[MenuPlugin()],
    )

    # Define a thread and invoke the agent with the user input
    thread = await agent.client.beta.threads.create()

    user_inputs = ["Hello", "What is the special soup?", "What is the special drink?", "Thank you"]
    try:
        for user_input in user_inputs:
            await agent.add_chat_message(
                thread_id=thread.id,
                message=user_input,
            )
            print(f"# User: '{user_input}'")
            async for content in agent.invoke(thread_id=thread.id):
                if content.role != AuthorRole.TOOL:
                    print(f"# Agent: {content.content}")

    finally:
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
    # Agent: You're welcome! If you have any more questions or need further assistance, feel free to ask. Enjoy your day!
    """


if __name__ == "__main__":
    asyncio.run(main())
