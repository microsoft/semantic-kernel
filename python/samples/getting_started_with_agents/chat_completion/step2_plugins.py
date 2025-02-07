# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import TYPE_CHECKING, Annotated

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatHistory
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.functions import KernelArguments, kernel_function

if TYPE_CHECKING:
    pass


###################################################################
# The following sample demonstrates how to create a simple,       #
# non-group agent that utilizes plugins defined as part of        #
# the Kernel.                                                     #
###################################################################


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
kernel.add_plugin(MenuPlugin(), plugin_name="menu")

service_id = "agent"
kernel.add_service(AzureChatCompletion(service_id=service_id))

settings = kernel.get_prompt_execution_settings_from_service_id(service_id=service_id)
# Configure the function choice behavior to auto invoke kernel functions
settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

# Define the agent name and instructions
AGENT_NAME = "Host"
AGENT_INSTRUCTIONS = "Answer questions about the menu."
# Create the agent
agent = ChatCompletionAgent(
    service_id=service_id,
    kernel=kernel,
    name=AGENT_NAME,
    instructions=AGENT_INSTRUCTIONS,
    arguments=KernelArguments(settings=settings),
)


async def main():
    # Define the chat history
    chat_history = ChatHistory()

    # Respond to user input
    user_inputs = [
        "Hello",
        "What is the special soup?",
        "What does that cost?",
        "Thank you",
    ]

    for user_input in user_inputs:
        # Add the user input to the chat history
        chat_history.add_user_message(user_input)
        print(f"# User: '{user_input}'")

        agent_name: str | None = None
        print("# Assistant - ", end="")
        async for content in agent.invoke_stream(chat_history):
            if not agent_name:
                agent_name = content.name
                print(f"{agent_name}: '", end="")
            if (
                not any(isinstance(item, (FunctionCallContent, FunctionResultContent)) for item in content.items)
                and content.content.strip()
            ):
                print(f"{content.content}", end="", flush=True)
        print("'")


if __name__ == "__main__":
    asyncio.run(main())
