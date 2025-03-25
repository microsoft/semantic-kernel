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


# Simulate a conversation with the agent
USER_INPUTS = [
    "Who is the youngest employee?",
    "Who works in sales?",
    "I have a customer request, who can help me?",
]


async def main():
    # 1. Create the client using Azure OpenAI resources and configuration
    client, model = OpenAIResponseAgent.setup_resources()

    computer_use_tool = OpenAIResponseAgent.configure_computer_use_tool(
        display_height=1080,
        display_width=1920,
        environment="mac",
    )

    # 2. Create a Semantic Kernel agent for the OpenAI Response API
    agent = OpenAIResponseAgent(
        ai_model_id=model,
        client=client,
        instructions="Leverage the computer use tool to answer questions about the world.",
        name="ComputerUse",
        tools=[computer_use_tool],
    )

    # 3. Create a thread for the agent
    # If no thread is provided, a new thread will be
    # created and returned with the initial response
    thread: ResponseAgentThread = None

    for user_input in USER_INPUTS:
        print(f"# User: '{user_input}'")
        # 4. Invoke the agent for the current message and print the response
        first_chunk = True
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
