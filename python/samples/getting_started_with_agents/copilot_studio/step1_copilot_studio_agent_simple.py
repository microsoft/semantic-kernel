# Copyright (c) Microsoft. All rights reserved.

import asyncio

from microsoft.agents.copilotstudio.client import (
    CopilotClient,
)

from semantic_kernel.agents import CopilotStudioAgent


async def main() -> None:
    client: CopilotClient = CopilotStudioAgent.setup_resources()

    agent = CopilotStudioAgent(
        client=client,
        name="PhysicsAgent",
        instructions="You are help answer questions about physics. ",
    )

    USER_INPUTS = [
        "Why is the sky blue?",
        "What is the speed of light?",
    ]

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
