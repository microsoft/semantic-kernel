# Copyright (c) Microsoft. All rights reserved.
import asyncio
from typing import Annotated

from semantic_kernel.agents.open_ai import AzureAssistantAgent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.functions.kernel_function_decorator import kernel_function

"""
The following sample demonstrates how to create an OpenAI
assistant using either Azure OpenAI or OpenAI. OpenAI Assistants
allow for function calling, the use of file search and a
code interpreter. Assistant Threads are used to manage the
conversation state, similar to a Semantic Kernel Chat History.
This sample also demonstrates the Assistants Streaming
capability and how to manage an Assistants chat history.
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
    # Create the client using Azure OpenAI resources and configuration
    client, model = AzureAssistantAgent.setup_resources()

    # Define the assistant definition
    definition = await client.beta.assistants.create(
        model=model,
        name="Host",
        instructions="Answer questions about the menu.",
    )

    # Create the AzureAssistantAgent instance using the client and the assistant definition and the defined plugin
    agent = AzureAssistantAgent(
        client=client,
        definition=definition,
        plugins=[MenuPlugin()],
    )

    thread = await client.beta.threads.create()

    user_inputs = ["Hello", "What is the special soup?", "What is the special drink?", "How much is that?", "Thank you"]

    try:
        for user_input in user_inputs:
            await agent.add_chat_message(thread_id=thread.id, message=user_input)

            print(f"# {AuthorRole.USER}: '{user_input}'")

            first_chunk = True
            async for content in agent.invoke_stream(thread_id=thread.id):
                if first_chunk:
                    print(f"# {content.role}: ", end="", flush=True)
                    first_chunk = False
                print(content.content, end="", flush=True)
            print()
    finally:
        await client.beta.threads.delete(thread.id)
        await client.beta.assistants.delete(assistant_id=agent.id)


if __name__ == "__main__":
    asyncio.run(main())
