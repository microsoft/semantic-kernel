# Copyright (c) Microsoft. All rights reserved.

import asyncio
import uuid

from samples.concepts.agents.bedrock_agent.setup_utils import use_existing_agent, use_new_agent

# This sample shows how to interact with a Bedrock agent in the simplest way.
# This sample uses the following main component(s):
# - a Bedrock agent
# You will learn how to create a new or connect to an existing Bedrock agent and talk to it.

# By default, this sample will create a new agent that will be deleted after the session ends.
# If you want to use an existing agent, set this to False and fill in required parameters.
CREATE_NEW_AGENT = True

# If you want to enable streaming, set this to True.
# In order to perform streaming, you need to have the permission on action: bedrock:InvokeModelWithResponseStream
STREAMING = False

# Common parameters whether creating a new agent or using an existing agent
AGENT_NAME = "semantic-kernel-bedrock-agent-simple-chat-sample"

# If creating a new agent, you need to specify the following:
INSTRUCTION = "You are a friendly assistant. You help people find information."

# If using an existing agent, you need to specify the following:
AGENT_ID = ""


async def main():
    if CREATE_NEW_AGENT:
        bedrock_agent = await use_new_agent(AGENT_NAME, INSTRUCTION)
    else:
        bedrock_agent = await use_existing_agent(AGENT_ID, AGENT_NAME)

    # Use a uiud as the session id
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

    if CREATE_NEW_AGENT:
        # Delete the agent if it was created in this session
        await bedrock_agent.delete_agent()


if __name__ == "__main__":
    asyncio.run(main())
