# Copyright (c) Microsoft. All rights reserved.

import asyncio

from microsoft.agents.copilotstudio.client import (
    CopilotClient,
)

from semantic_kernel.agents import CopilotStudioAgent, CopilotStudioAgentThread


async def main() -> None:
    client: CopilotClient = CopilotStudioAgent.setup_resources()

    agent = CopilotStudioAgent(
        client=client,
        name="PhysicsAgent",
        instructions="You are help answer questions about physics. ",
    )

    USER_INPUTS = [
        "Hello! Who are you? My name is John Doe.",
        "What is the speed of light?",
        "What have we been talking about?",
        "What is my name?",
    ]

    thread: CopilotStudioAgentThread | None = None

    for user_input in USER_INPUTS:
        print(f"# User: {user_input}")
        response = await agent.get_response(messages=user_input, thread=thread)
        print(f"# {response.name}: {response}")
        thread = response.thread

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
