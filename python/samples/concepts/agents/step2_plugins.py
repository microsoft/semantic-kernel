# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Annotated

from semantic_kernel.agents.chat_completion_agent import ChatCompletionAgent
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel

###################################################################
# The following sample demonstrates how to create a simple,       #
# non-group agent that utilizes plugins defined as part of        #
# the Kernel.                                                     #
###################################################################

# Define the agent name and instructions
HOST_NAME = "Host"
HOST_INSTRUCTIONS = "Answer questions about the menu."


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


# A helper method to invoke the agent with the user input
async def invoke_agent(agent: ChatCompletionAgent, input: str, kernel: Kernel, chat: ChatHistory) -> None:
    """Invoke the agent with the user input."""
    chat.add_user_message(input)

    print(f"# {AuthorRole.USER}: '{input}'")

    async for content in agent.invoke(kernel, chat):
        print(f"# {content.role} - {content.name or '*'}: '{content.content}'")


async def main():
    # Create the instance of the Kernel
    kernel = Kernel()

    # Add the OpenAIChatCompletion AI Service to the Kernel
    service_id = "agent"
    kernel.add_service(AzureChatCompletion(service_id=service_id))

    settings = kernel.get_prompt_execution_settings_from_service_id(service_id=service_id)
    # Configure the function choice behavior to auto invoke kernel functions
    settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

    # Create the agent
    agent = ChatCompletionAgent(
        service_id="agent", name=HOST_NAME, instructions=HOST_INSTRUCTIONS, execution_settings=settings
    )

    kernel.add_plugin(plugin=MenuPlugin(), plugin_name="menu")

    # Define the chat history
    chat = ChatHistory()

    # Respond to user input
    await invoke_agent(agent, "Hello", kernel, chat)
    await invoke_agent(agent, "What is the special soup?", kernel, chat)
    await invoke_agent(agent, "What is the special drink?", kernel, chat)
    await invoke_agent(agent, "Thank you", kernel, chat)


if __name__ == "__main__":
    asyncio.run(main())
