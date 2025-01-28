# Copyright (c) Microsoft. All rights reserved.

import os

import dotenv

from semantic_kernel.agents.bedrock.bedrock_agent import BedrockAgent

dotenv.load_dotenv()

# Common parameters whether creating a new agent or using an existing agent
AGENT_ROLE_AMAZON_RESOURCE_NAME = os.getenv("AGENT_ROLE_AMAZON_RESOURCE_NAME")

# If creating a new agent, you need to specify the following:
# [Note] You may have to request access to the foundation model if you don't have it.
# [Note] When using function calling, the success rate of function calling may vary
#        depending on the foundation model. Advanced models may have better performance.
FOUNDATION_MODEL = os.getenv("FOUNDATION_MODEL")


async def use_new_agent(agent_name: str, instruction: str, **kwargs):
    """Create a new bedrock agent."""
    return await BedrockAgent.create_new_agent(
        agent_name=agent_name,
        foundation_model=FOUNDATION_MODEL,
        role_arn=AGENT_ROLE_AMAZON_RESOURCE_NAME,
        instruction=instruction,
        **kwargs,
    )


async def use_existing_agent(agent_id: str, agent_name: str, **kwargs):
    """Use an existing bedrock agent that has been created and prepared."""
    return await BedrockAgent.use_existing_agent(
        agent_arn=AGENT_ROLE_AMAZON_RESOURCE_NAME,
        agent_id=agent_id,
        agent_name=agent_name,
        **kwargs,
    )
