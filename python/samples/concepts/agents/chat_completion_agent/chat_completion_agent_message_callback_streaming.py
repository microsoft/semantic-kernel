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


intermediate_steps: list[ChatMessageContent] = []


async def handle_streaming_intermediate_steps(message: ChatMessageContent) -> None:
    intermediate_steps.append(message)


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
        first_chunk = True
        async for response in agent.invoke_stream(
            messages=user_input,
            thread=thread,
            on_intermediate_message=handle_streaming_intermediate_steps,
        ):
            if first_chunk:
                print(f"# {response.name}: ", end="", flush=True)
                first_chunk = False
            if response.content:
                print(response.content, end="", flush=True)
            thread = response.thread
        print()

    # Print the intermediate steps
    print("\nIntermediate Steps:")
    for msg in intermediate_steps:
        if any(isinstance(item, FunctionResultContent) for item in msg.items):
            for fr in msg.items:
                if isinstance(fr, FunctionResultContent):
                    print(f"Function Result:> {fr.result} for function: {fr.name}")
        elif any(isinstance(item, FunctionCallContent) for item in msg.items):
            for fcc in msg.items:
                if isinstance(fcc, FunctionCallContent):
                    print(f"Function Call:> {fcc.name} with arguments: {fcc.arguments}")
        else:
            print(f"{msg.role}: {msg.content}")

    # Sample output:
    # User: 'Hello'
    # AuthorRole.ASSISTANT: Hello! How can I assist you today? If you have any questions about the menu,
    #                       feel free to ask!
    # User: 'What is the special soup?'
    # AuthorRole.ASSISTANT: The special soup is Clam Chowder. Would you like to know more about it or
    #                       anything else on the menu?
    # User: 'How much does that cost?'
    # AuthorRole.ASSISTANT: The Clam Chowder costs $9.99. If you have any other questions or need further
    #                       information, feel free to ask!
    # User: 'Thank you'
    # AuthorRole.ASSISTANT: You're welcome! If you have any more questions in the future, don't hesitate
    #                       to ask. Have a great day!
    #
    # Intermediate Steps:
    # Function Call:> MenuPlugin-get_specials with arguments: {}
    # Function Result:>
    #         Special Soup: Clam Chowder
    #         Special Salad: Cobb Salad
    #         Special Drink: Chai Tea
    #         for function: MenuPlugin-get_specials
    # Function Call:> MenuPlugin-get_item_price with arguments: {"menu_item":"Clam Chowder"}
    # Function Result:> $9.99 for function: MenuPlugin-get_item_price


if __name__ == "__main__":
    asyncio.run(main())
