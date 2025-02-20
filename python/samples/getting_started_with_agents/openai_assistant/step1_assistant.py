# Copyright (c) Microsoft. All rights reserved.
import asyncio
from typing import Annotated

from semantic_kernel import Kernel
from semantic_kernel.agents.open_ai import OpenAIAssistantAgent
from semantic_kernel.contents import AuthorRole
from semantic_kernel.functions import kernel_function

#####################################################################
# The following sample demonstrates how to create an OpenAI         #
# assistant using either Azure OpenAI or OpenAI. OpenAI Assistants  #
# allow for function calling, the use of file search and a          #
# code interpreter. Assistant Threads are used to manage the        #
# conversation state, similar to a Semantic Kernel Chat History.    #
#####################################################################


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


# Create the instance of the Kernel
kernel = Kernel()

# Add the sample plugin to the kernel
kernel.add_plugin(plugin=MenuPlugin(), plugin_name="menu")


async def main():
    # Create the OpenAI Assistant Agent
    client = OpenAIAssistantAgent.create_openai_client()

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
            async for content in agent.invoke(thread_id=thread_id):
                if content.role != AuthorRole.TOOL:
                    print(f"# Agent: {content.content}")

    finally:
        await agent.client.beta.threads.delete(thread.id)
        await agent.client.beta.assistants.delete(assistant_id=agent.id)


if __name__ == "__main__":
    asyncio.run(main())
