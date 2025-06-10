# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Annotated

from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.completion_usage import CompletionUsage
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import kernel_function

"""
The following sample demonstrates how to create a chat completion agent
and use it with streaming responses. It also shows how to track token 
usage during the streaming process.
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

    completion_usage = CompletionUsage()

    for user_input in user_inputs:
        print(f"\n# User: '{user_input}'")
        async for response in agent.invoke_stream(
            messages=user_input,
            thread=thread,
        ):
            if response.content:
                print(response.content, end="", flush=True)
            if response.metadata.get("usage"):
                completion_usage += response.metadata["usage"]
                print(f"\nStreaming Usage: {response.metadata['usage']}")
            thread = response.thread
        print()

    # Print the completion usage
    print(f"\nStreaming Total Completion Usage: {completion_usage.model_dump_json(indent=4)}")

    """
    Sample Output:

    # User: 'Hello'
    Hello! How can I help you with the menu today?

    # User: 'What is the special soup?'
    The special soup today is Clam Chowder. Would you like more details or are you interested in something else from 
        the menu?

    # User: 'How much does that cost?'
    The Clam Chowder special soup costs $9.99. Would you like to add it to your order or ask about something else?

    # User: 'Thank you'
    You're welcome! If you have any more questions or need help with the menu, just let me know. Enjoy your meal!

    Streaming Total Completion Usage: {
        "prompt_tokens": 1150,
        "prompt_tokens_details": {
            "audio_tokens": 0,
            "cached_tokens": 0
        },
        "completion_tokens": 134,
        "completion_tokens_details": {
            "accepted_prediction_tokens": 0,
            "audio_tokens": 0,
            "reasoning_tokens": 0,
            "rejected_prediction_tokens": 0
        }
    }
    """


if __name__ == "__main__":
    asyncio.run(main())
