# Copyright (c) Microsoft. All rights reserved.
import asyncio
from typing import Annotated

from semantic_kernel import Kernel
from semantic_kernel.agents.open_ai import AzureAssistantAgent, OpenAIAssistantAgent
from semantic_kernel.contents import AuthorRole, ChatMessageContent
from semantic_kernel.functions import kernel_function

#####################################################################
# The following sample demonstrates how to create an OpenAI         #
# assistant using either Azure OpenAI or OpenAI. OpenAI Assistants  #
# allow for function calling, the use of file search and a          #
# code interpreter. Assistant Threads are used to manage the        #
# conversation state, similar to a Semantic Kernel Chat History.    #
#####################################################################


# Note: you may toggle this to switch between AzureOpenAI and OpenAI
use_azure_openai = False


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
    HOST_NAME = "Host"
    HOST_INSTRUCTIONS = "Answer questions about the menu."

    # Create the OpenAI Assistant Agent
    service_id = "agent"
    if use_azure_openai:
        agent = await AzureAssistantAgent.create(
            kernel=kernel, service_id=service_id, name=HOST_NAME, instructions=HOST_INSTRUCTIONS
        )
    else:
        agent = await OpenAIAssistantAgent.create(
            kernel=kernel, service_id=service_id, name=HOST_NAME, instructions=HOST_INSTRUCTIONS
        )

    thread_id = await agent.create_thread()

    user_inputs = ["Hello", "What is the special soup?", "What is the special drink?", "Thank you"]
    try:
        for user_input in user_inputs:
            await agent.add_chat_message(
                thread_id=thread_id, message=ChatMessageContent(role=AuthorRole.USER, content=user_input)
            )
            print(f"# User: '{user_input}'")
            async for content in agent.invoke(thread_id=thread_id):
                if content.role != AuthorRole.TOOL:
                    print(f"# Agent: {content.content}")

    finally:
        await agent.delete_thread(thread_id)
        await agent.delete()


if __name__ == "__main__":
    asyncio.run(main())
