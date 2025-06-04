# Copyright (c) Microsoft. All rights reserved.

import asyncio

from microsoft.agents.copilotstudio.client import (
    CopilotClient,
)

from semantic_kernel.agents import CopilotStudioAgent, CopilotStudioAgentThread

"""
This sample demonstrates how to use the Copilot Studio agent to answer questions from the user.
It demonstrates how to use a thread to maintain context between user inputs.
"""


async def main() -> None:
    # As an example, manually create the client and pass it in to the agent
    # 1. Create the client
    client: CopilotClient = CopilotStudioAgent.create_client(auth_mode="interactive")

    # 2. Create the agent
    agent = CopilotStudioAgent(
        client=client,
        name="PhysicsAgent",
        instructions="You are help answer questions about physics.",
    )

    # 3. Create a list of user inputs
    USER_INPUTS = [
        "Hello! Who are you? My name is John Doe.",
        "What is the speed of light?",
        "What have we been talking about?",
        "What is my name?",
    ]

    # 4. Create a thread to maintain context between user inputs
    # If no thread is provided, a new thread will be created
    # and returned in the response
    thread: CopilotStudioAgentThread | None = None

    # 5. Loop through the user inputs and get responses from the agent
    for user_input in USER_INPUTS:
        print(f"# User: {user_input}")
        response = await agent.get_response(messages=user_input, thread=thread)
        print(f"# {response.name}: {response}")
        thread = response.thread

    # 6. If a thread was created, delete it when done
    if thread:
        await thread.delete()

    """
    Sample output:

    # User: Hello! Who are you? My name is John Doe.
    # PhysicsAgent: Hello, John! I'm an AI assistant here to help you with any questions you might have. 
        How can I assist you today?
    AI-generated content may be incorrect
    # User: What is the speed of light?
    # PhysicsAgent: The speed of light in a vacuum is approximately 299,792,458 meters per second (m/s). 
        This is often rounded to 300,000 kilometers per second (km/s) for simplicity. If you have any more questions, 
        feel free to ask!
    AI-generated content may be incorrect
    # User: What have we been talking about?
    # PhysicsAgent: Sure, John! So far, we've had the following conversation:

    1. You introduced yourself and asked who I am.
    2. I introduced myself as an AI assistant and asked how I could assist you.
    3. You asked about the speed of light, and I provided the information that it is approximately 299,792,458 meters 
        per second in a vacuum.

    If you have any more questions or need further assistance, feel free to ask!
    AI-generated content may be incorrect
    # User: What is my name?
    # PhysicsAgent: Based on our conversation, your name is John Doe. How can I assist you further today?
    AI-generated content may be incorrect
    """


if __name__ == "__main__":
    asyncio.run(main())
