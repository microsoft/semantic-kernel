# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents import CopilotStudioAgent

"""
This sample demonstrates how to use the Copilot Studio agent to answer questions about physics.
It does not use a thread to maintain context between user inputs.
"""


async def main() -> None:
    # 1. Create the agent
    agent = CopilotStudioAgent(
        name="PhysicsAgent",
        instructions="You help answer questions about physics. ",
    )

    # 2. Create a list of user inputs
    USER_INPUTS = [
        "Why is the sky blue?",
        "What is the speed of light?",
    ]

    # 3. Loop through the user inputs and get responses from the agent
    for user_input in USER_INPUTS:
        print(f"# User: {user_input}")
        response = await agent.get_response(messages=user_input)
        print(f"# {response.name}: {response}")

    """
    Sample output:

    # User: Why is the sky blue?
    # PhysicsAgent: The sky appears blue because of the way Earth's atmosphere scatters sunlight. 
        When sunlight enters the atmosphere, it is made up of different colors, each with different wavelengths. 
        Blue light has shorter wavelengths and is scattered in all directions by the gases and particles in the 
        atmosphere more than other colors. This scattered blue light is what we see when we look up at the sky. 
        This phenomenon is known as Rayleigh scattering.
        AI-generated content may be incorrect
    # User: What is the speed of light?
    # PhysicsAgent: The speed of light in a vacuum is approximately 299,792,458 meters per second (m/s). This is often 
        rounded to 300,000 kilometers per second (km/s) for simplicity.
        AI-generated content may be incorrect
    """


if __name__ == "__main__":
    asyncio.run(main())
