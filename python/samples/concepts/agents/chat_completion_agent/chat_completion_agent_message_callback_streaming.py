# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Annotated

from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatMessageContent, FunctionCallContent, FunctionResultContent
from semantic_kernel.functions import kernel_function

"""
The following sample demonstrates how to create a chat completion agent
and use it with streaming responses. Additionally, the invoke_stream
configures a message callback to receive fully formed messages once
the streaming invocation is complete. The agent is configured to use
a plugin that provides a list of specials from the menu and the price
of the requested menu item.
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


# This callback function will be called for each intermediate message
# Which will allow one to handle FunctionCallContent and FunctionResultContent
# If the callback is not provided, the agent will return the final response
# with no intermediate tool call steps.
async def handle_streaming_intermediate_steps(message: ChatMessageContent) -> None:
    for item in message.items or []:
        if isinstance(item, FunctionCallContent):
            print(f"Function Call:> {item.name} with arguments: {item.arguments}")
        elif isinstance(item, FunctionResultContent):
            print(f"Function Result:> {item.result} for function: {item.name}")
        else:
            print(f"{message.role}: {message.content}")


async def main() -> None:
    agent = ChatCompletionAgent(
        service=AzureChatCompletion(),
        name="Assistant",
        instructions="Answer questions about the menu.",
        plugins=[MenuPlugin()],
    )

    # Create a thread for the agent
    # If no thread is provided, a new thread will be
    # created and returned with the initial response
    thread: ChatHistoryAgentThread = None

    user_inputs = [
        "Hello",
        "What is the special soup?",
        "How much does that cost?",
        "Thank you",
    ]

    for user_input in user_inputs:
        print(f"\n# User: '{user_input}'")
        async for response in agent.invoke_stream(
            messages=user_input,
            thread=thread,
            on_intermediate_message=handle_streaming_intermediate_steps,
        ):
            if response.content:
                print(response.content, end="", flush=True)
            thread = response.thread
        print()

    """
    Sample Output:

    # User: 'Hello'
    Hello! How can I assist you today?

    # User: 'What is the special soup?'
    Function Call:> MenuPlugin-get_specials with arguments: {}
    Function Result:> 
            Special Soup: Clam Chowder
            Special Salad: Cobb Salad
            Special Drink: Chai Tea
            for function: MenuPlugin-get_specials
    The special soup today is Clam Chowder. Is there anything else you'd like to know?

    # User: 'How much does that cost?'
    Function Call:> MenuPlugin-get_item_price with arguments: {"menu_item":"Clam Chowder"}
    Function Result:> $9.99 for function: MenuPlugin-get_item_price
    The Clam Chowder costs $9.99. Would you like to know anything else about the menu?

    # User: 'Thank you'
    You're welcome! If you have any more questions, feel free to ask. Have a great day!
    """


if __name__ == "__main__":
    asyncio.run(main())
