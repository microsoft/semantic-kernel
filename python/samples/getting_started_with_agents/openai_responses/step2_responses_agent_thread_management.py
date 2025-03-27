# Copyright (c) Microsoft. All rights reserved.
import asyncio

from semantic_kernel.agents import AzureResponsesAgent

"""
The following sample demonstrates how to create an OpenAI Responses Agent.
The sample shows how to have the assistant answer questions about the world.

The interaction with the agent is via the `get_response` method, which sends a
user input to the agent and receives a response from the agent. The conversation
history is maintained by the agent service, i.e. the responses are automatically
associated with the thread. Therefore, client code does not need to maintain the
conversation history.
"""

USER_INPUTS = [
    "Tell me a joke",
    "Explain why this is funny.",
    "What have we been talking about?",
]


async def main():
    # 1. Create the client using Azure OpenAI resources and configuration
    client, model = AzureResponsesAgent.setup_resources()

    # 2. Create a Semantic Kernel agent for the OpenAI Responses API
    agent = AzureResponsesAgent(
        ai_model_id=model,
        client=client,
        instructions="Answer questions about from the user.",
        name="Joker",
    )

    # 3. Create a thread for the agent
    # If no thread is provided, a new thread will be
    # created and returned with the initial response
    thread = None

    for user_input in USER_INPUTS:
        print(f"# User: '{user_input}'")
        # 4. Invoke the agent for the current message and print the response
        response = await agent.get_response(messages=user_input, thread=thread)
        print(f"# {response.name}: {response.content}")
        # 5. Update the thread so the previous response id is used
        thread = response.thread

    """
    You should see output similar to the following:

    # User: 'Tell me a joke'
    # Joker: Why don't skeletons fight each other? They don't have the guts!
    # User: 'Explain why this is funny.'
    # Joker: The joke is funny because it plays on the double meaning of "guts"—literally referring to internal organs, 
        which skeletons lack, and metaphorically meaning courage.
    # User: 'What have we been talking about?'
    # Joker: We've been discussing a skeleton joke and why it's funny.
     """


if __name__ == "__main__":
    asyncio.run(main())
