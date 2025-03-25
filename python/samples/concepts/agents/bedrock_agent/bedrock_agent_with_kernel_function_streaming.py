# Copyright (c) Microsoft. All rights reserved.

import asyncio
from typing import Annotated

from semantic_kernel.agents import BedrockAgent, BedrockAgentThread
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel

"""
This sample shows how to interact with a Bedrock agent that is capable of using kernel functions.
This sample uses the following main component(s):
- a Bedrock agent
- a kernel function
- a kernel
You will learn how to create a new Bedrock agent and ask it a question that requires a kernel function to answer.
"""

AGENT_NAME = "semantic-kernel-bedrock-agent"
INSTRUCTION = "You are a friendly assistant. You help people find information."


class WeatherPlugin:
    """Mock weather plugin."""

    @kernel_function(description="Get real-time weather information.")
    def current(self, location: Annotated[str, "The location to get the weather"]) -> str:
        """Returns the current weather."""
        return f"The weather in {location} is sunny."


def get_kernel() -> Kernel:
    kernel = Kernel()
    kernel.add_plugin(WeatherPlugin(), plugin_name="weather")

    return kernel


async def main():
    # Create a kernel
    kernel = get_kernel()

    bedrock_agent = await BedrockAgent.create_and_prepare_agent(
        AGENT_NAME,
        INSTRUCTION,
        kernel=kernel,
    )
    # Note: We still need to create the kernel function action group on the service side.
    await bedrock_agent.create_kernel_function_action_group()

    thread: BedrockAgentThread = None

    try:
        # Invoke the agent
        print("Response: ")
        async for response in bedrock_agent.invoke_stream(
            messages="What is the weather in Seattle?",
            thread=thread,
        ):
            print(response, end="")
            thread = response.thread
    finally:
        # Delete the agent
        await bedrock_agent.delete_agent()
        await thread.delete() if thread else None

    # Sample output (using anthropic.claude-3-haiku-20240307-v1:0):
    # Response:
    # The current weather in Seattle is sunny.


if __name__ == "__main__":
    asyncio.run(main())
