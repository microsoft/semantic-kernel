# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Annotated

from pydantic import BaseModel

from semantic_kernel import Kernel
from semantic_kernel.agents import AgentRegistry, ChatHistoryAgentThread
from semantic_kernel.agents.chat_completion.chat_completion_agent import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
    AzureChatPromptExecutionSettings,
)
from semantic_kernel.functions import KernelArguments, kernel_function

"""
The following sample demonstrates how to create a chat completion agent using a 
declarative approach. The Chat Completion Agent is created from a YAML spec,
with a specific service and plugins. The agent is then used to answer user questions.

This sample also demonstrates how to properly pass execution settings (like response format)
when using AgentRegistry.create_from_yaml().
"""


# Example structure for structured output
class StructuredResult(BaseModel):
    """Example structure for demonstrating response format."""

    response: str
    category: str


# 1. Define a Sample Plugin
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


# 2. Define the YAML string
AGENT_YAML = """
type: chat_completion_agent
name: Assistant
description: A helpful assistant.
instructions: Answer the user's questions using the menu functions.
tools:
  - id: MenuPlugin.get_specials
    type: function
  - id: MenuPlugin.get_item_price
    type: function
model:
  options:
    temperature: 0.7
"""

# 3. Define your simulated conversation
USER_INPUTS = [
    "Hello",
    "What is the special soup?",
    "What does that cost?",
    "Thank you",
]


async def main():
    # 4. Create a Kernel and add the plugin
    # For declarative agents, the kernel is required to resolve the plugin
    kernel = Kernel()
    kernel.add_plugin(MenuPlugin(), plugin_name="MenuPlugin")

    # 5. Create execution settings with structured output
    execution_settings = AzureChatPromptExecutionSettings()
    execution_settings.response_format = StructuredResult

    # 6. Create KernelArguments with the execution settings
    arguments = KernelArguments(settings=execution_settings)

    # 7. Create the agent from YAML + inject the AI service
    agent: ChatCompletionAgent = await AgentRegistry.create_from_yaml(
        AGENT_YAML, kernel=kernel, service=AzureChatCompletion(), arguments=arguments
    )

    # 8. Create a thread to hold the conversation
    thread: ChatHistoryAgentThread | None = None

    for user_input in USER_INPUTS:
        print(f"# User: {user_input}")
        # 9. Invoke the agent for a response
        response = await agent.get_response(messages=user_input, thread=thread)
        print(f"# {response.name}: {response}")
        thread = response.thread

    # 10. Cleanup the thread
    await thread.delete() if thread else None

    """
    # Sample output:

    # User: Hello
    # Assistant: {"response":"Hello! How can I help you today? If you have any questions about the menu, feel free to ask!","category":"Greeting"}
    # User: What is the special soup?
    # Assistant: {"response":"Today's special soup is Clam Chowder. Would you like to know more about it or see other specials?","category":"Menu Specials"}
    # User: What does that cost?
    # Assistant: {"response":"The Clam Chowder special soup costs $9.99.","category":"Menu Pricing"}
    # User: Thank you
    # Assistant: {"response":"You're welcome! If you have any more questions or need assistance with the menu, just let me know. Enjoy your meal!","category":"Polite Closing"}
    """  # noqa: E501


if __name__ == "__main__":
    asyncio.run(main())
