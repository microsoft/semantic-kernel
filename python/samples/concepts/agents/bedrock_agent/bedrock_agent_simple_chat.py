# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
import uuid

import dotenv

from semantic_kernel.agents.bedrock.bedrock_agent import BedrockAgent

dotenv.load_dotenv()

# By default, this sample will create a new agent.
# If you want to use an existing agent, set this to False and fill in required parameters.
CREATE_NEW_AGENT = True

# If you want to enable streaming, set this to True.
# In order to perform streaming, you need to have the permission on action: bedrock:InvokeModelWithResponseStream
STREAMING = False

# Common parameters whether creating a new agent or using an existing agent
AGENT_ROLE_AMAZON_RESOURCE_NAME = os.getenv("AGENT_ROLE_AMAZON_RESOURCE_NAME")
AGENT_NAME = "semantic-kernel-bedrock-agent-simple-chat-sample"

# If creating a new agent, you need to specify the following:
# [Note] You may have to request access to the foundation model if you don't have it.
FOUNDATION_MODEL = os.getenv("FOUNDATION_MODEL")
INSTRUCTION = "You are a fridenly assistant. You help people find information."

# If using an existing agent, you need to specify the following:
AGENT_ID = ""


async def use_new_agent():
    """Create a new bedrock agent."""
    return await BedrockAgent.create_new_agent(
        agent_name=AGENT_NAME,
        foundation_model=FOUNDATION_MODEL,
        role_arn=AGENT_ROLE_AMAZON_RESOURCE_NAME,
        instruction=INSTRUCTION,
    )


async def use_existing_agent():
    """Use an existing bedrock agent that has been created and prepared."""
    return await BedrockAgent.use_existing_agent(
        agent_arn=AGENT_ROLE_AMAZON_RESOURCE_NAME,
        agent_id=AGENT_ID,
        agent_name=AGENT_NAME,
    )


async def main():
    if CREATE_NEW_AGENT:
        bedrock_agent = await use_new_agent()
    else:
        bedrock_agent = await use_existing_agent()

    # Use an uiud as the session id
    new_session_id = str(uuid.uuid4())

    # Invoke the agent
    if STREAMING:
        print("Response: ")
        async for response in bedrock_agent.invoke_stream(
            session_id=new_session_id,
            input_text="Hi, how are you?",
        ):
            print(response, end="")
    else:
        async for response in bedrock_agent.invoke(
            session_id=new_session_id,
            input_text="Hi, how are you?",
        ):
            print(f"Response:\n{response}")


if __name__ == "__main__":
    asyncio.run(main())
