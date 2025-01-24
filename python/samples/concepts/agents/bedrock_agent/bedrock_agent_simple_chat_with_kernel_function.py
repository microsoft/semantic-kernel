# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
import uuid
from typing import Annotated

import dotenv

from semantic_kernel.agents.bedrock.bedrock_agent import BedrockAgent
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel

dotenv.load_dotenv()


# By default, this sample will create a new agent.
# If you want to use an existing agent, set this to False and fill in required parameters.
CREATE_NEW_AGENT = True

# If you want to enable streaming, set this to True.
# In order to perform streaming, you need to have the permission on action: bedrock:InvokeModelWithResponseStream
STREAMING = False

# Common parameters whether creating a new agent or using an existing agent
AGENT_ROLE_AMAZON_RESOURCE_NAME = os.getenv("AGENT_ROLE_AMAZON_RESOURCE_NAME")
AGENT_NAME = "semantic-kernel-bedrock-agent-simple-chat-kernel-function-sample"

# If creating a new agent, you need to specify the following:
# [Note] You may have to request access to the foundation model if you don't have it.
# [Note] The success rate of function calling may vary depending on the foundation model.
#        Advanced models may have better performance.
FOUNDATION_MODEL = os.getenv("FOUNDATION_MODEL")
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


async def use_new_agent(kernel: Kernel):
    """Create a new bedrock agent."""
    bedrock_agent = await BedrockAgent.create_new_agent(
        agent_name=AGENT_NAME,
        foundation_model=FOUNDATION_MODEL,
        role_arn=AGENT_ROLE_AMAZON_RESOURCE_NAME,
        instruction=INSTRUCTION,
        kernel=kernel,
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
    )

    # Create a kernel function action group on the Bedrock agent service.
    await bedrock_agent.create_kernel_function_action_group()

    return bedrock_agent


async def use_existing_agent(kernel: Kernel):
    """Use an existing bedrock agent that has been created and prepared.

    Make sure the existing agent has the action group created for the kernel function.
    """
    return await BedrockAgent.use_existing_agent(
        agent_arn=AGENT_ROLE_AMAZON_RESOURCE_NAME,
        agent_id=AGENT_ID,
        agent_name=AGENT_NAME,
        kernel=kernel,
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
    )


async def main():
    # Create a kernel
    kernel = get_kernel()

    if CREATE_NEW_AGENT:
        bedrock_agent = await use_new_agent(kernel)
    else:
        bedrock_agent = await use_existing_agent(kernel)

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


if __name__ == "__main__":
    asyncio.run(main())
