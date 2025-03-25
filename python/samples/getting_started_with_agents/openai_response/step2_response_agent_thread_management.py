# Copyright (c) Microsoft. All rights reserved.
import asyncio

from semantic_kernel.agents import OpenAIResponseAgent, ResponseAgentThread

"""
The following sample demonstrates how to create an OpenAI assistant using either
Azure OpenAI or OpenAI. The sample shows how to have the assistant answrer
questions about the world.

The interaction with the agent is via the `get_response` method, which sends a
user input to the agent and receives a response from the agent. The conversation
history is maintained by the agent service, i.e. the responses are automatically
associated with the thread. Therefore, client code does not need to maintain the
conversation history.
"""

USER_INPUTS = [
    "Why is the sky blue?",
    "What is the speed of light?",
]


async def main():
    # 1. Create the client using Azure OpenAI resources and configuration
    client, model = OpenAIResponseAgent.setup_resources()

    # 2. Create a Semantic Kernel agent for the OpenAI Response API
    agent = OpenAIResponseAgent(
        ai_model_id=model,
        client=client,
        instructions="Answer questions about the world in one sentence.",
        name="Expert",
    )

    # 3. Create a thread for the agent
    # If no thread is provided, a new thread will be
    # created and returned with the initial response
    thread: ResponseAgentThread = None

    for user_input in USER_INPUTS:
        print(f"# User: '{user_input}'")
        # 4. Invoke the agent for the current message and print the response
        response = await agent.get_response(messages=user_input, thread=thread)
        print(f"# {response.name}: {response.content}")
        thread = response.thread

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
