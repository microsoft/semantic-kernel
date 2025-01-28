# Copyright (c) Microsoft. All rights reserved.

import asyncio
import uuid
from typing import Annotated

from samples.concepts.agents.bedrock_agent.setup_utils import use_existing_agent, use_new_agent
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel

# This sample shows how to interact with a Bedrock agent that is capable of using kernel functions.
# This sample uses the following main component(s):
# - a Bedrock agent
# - a kernel function
# - a kernel
# You will learn how to create a new or connect to an existing Bedrock agent and ask it a question
# that requires a kernel function to answer.

# By default, this sample will create a new agent that will be deleted after the session ends.
# If you want to use an existing agent, set this to False and fill in required parameters.
CREATE_NEW_AGENT = True

# If you want to enable streaming, set this to True.
# In order to perform streaming, you need to have the permission on action: bedrock:InvokeModelWithResponseStream
STREAMING = False

# Common parameters whether creating a new agent or using an existing agent
AGENT_NAME = "semantic-kernel-bedrock-agent-simple-chat-kernel-function-sample"

# If creating a new agent, you need to specify the following:
INSTRUCTION = "You are a fridenly assistant. You help people find information."

# If using an existing agent, you need to specify the following:
AGENT_ID = ""


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

    if CREATE_NEW_AGENT:
        bedrock_agent = await use_new_agent(
            AGENT_NAME,
            INSTRUCTION,
            enable_kernel_function=True,
            kernel=kernel,
        )
    else:
        bedrock_agent = await use_existing_agent(AGENT_ID, AGENT_NAME, kernel=kernel)

    # Use an uiud as the session id
    new_session_id = str(uuid.uuid4())

    # Invoke the agent
    if STREAMING:
        print("Response: ")
        async for response in bedrock_agent.invoke_stream(
            session_id=new_session_id,
            input_text="What is the weather in Seattle?",
        ):
            print(response, end="")
    else:
        async for response in bedrock_agent.invoke(
            session_id=new_session_id,
            input_text="What is the weather in Seattle?",
        ):
            print(f"Response:\n{response}")

    if CREATE_NEW_AGENT:
        # Delete the agent if it was created in this session
        await bedrock_agent.delete_agent()


if __name__ == "__main__":
    asyncio.run(main())
