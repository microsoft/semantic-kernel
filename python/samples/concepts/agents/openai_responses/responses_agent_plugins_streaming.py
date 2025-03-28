# Copyright (c) Microsoft. All rights reserved.
import asyncio
from typing import Annotated

from semantic_kernel.agents import OpenAIResponsesAgent, ResponsesAgentThread
from semantic_kernel.functions import kernel_function

"""
The following sample demonstrates how to create an OpenAI Responses Agent.
The sample shows how to have the agent answer questions about the sample menu
with streaming responses.

The interaction with the agent is via the `get_response` method, which sends a
user input to the agent and receives a response from the agent. The conversation
history is maintained by the agent service, i.e. the responses are automatically
associated with the thread. Therefore, client code does not need to maintain the
conversation history.
"""


# Define a sample plugin for the sample
class MenuPlugin:
    """A sample Menu Plugin used for the concept sample."""

    @kernel_function(description="Provides a list of specials from the menu.")
    def get_specials(self, menu_item: str) -> Annotated[str, "Returns the specials from the menu."]:
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


# Simulate a conversation with the agent
USER_INPUTS = [
    "Hello",
    "What is the special soup?",
    "What is the special drink?",
    "How much is it?",
    "Thank you",
]


async def main():
    # 1. Create the client using Azure OpenAI resources and configuration
    client, model = OpenAIResponsesAgent.setup_resources()

    # 2. Create a Semantic Kernel agent for the OpenAI Response API
    agent = OpenAIResponsesAgent(
        ai_model_id=model,
        client=client,
        instructions="Answer questions about the menu.",
        name="Host",
        plugins=[MenuPlugin()],
    )

    # 3. Create a thread for the agent
    # If no thread is provided, a new thread will be
    # created and returned with the initial response
    thread: ResponsesAgentThread = None

    for user_input in USER_INPUTS:
        print(f"# User: '{user_input}'")
        first_chunk = True
        # 4. Invoke the agent for the current message and print the response
        async for response in agent.invoke_stream(messages=user_input, thread=thread):
            thread = response.thread
            if first_chunk:
                print(f"# {response.name}: ", end="", flush=True)
                first_chunk = False
            print(response.content, end="", flush=True)
        print()

    """
    You should see output similar to the following:

    # User: 'Why is the sky blue?'
    # Agent: The sky appears blue because molecules in the atmosphere scatter sunlight in all directions, and blue 
        light is scattered more than other colors because it travels in shorter, smaller waves.
    # User: 'What is the speed of light?'
    # Agent: The speed of light in a vacuum is approximately 299,792,458 meters per second 
        (about 186,282 miles per second).
     """


if __name__ == "__main__":
    asyncio.run(main())
