# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.agents.agent import AgentRegistry
from semantic_kernel.kernel import Kernel

"""
The following sample demonstrates how to create an Azure AI agent that answers
user questions. This sample demonstrates the basic steps to create an agent
and simulate a conversation with the agent.

The interaction with the agent is via the `get_response` method, which sends a
user input to the agent and receives a response from the agent. The conversation
history is maintained by the agent service, i.e. the responses are automatically
associated with the thread. Therefore, client code does not need to maintain the
conversation history.
"""

spec = """
type: foundry_agent
name: MyAgent
description: My helpful agent.
instructions: You are helpful agent.
model:
  id: ${AzureAI:ChatModelId}
  connection:
    connection_string: ${AzureAI:ConnectionString}
"""


settings = AzureAIAgentSettings()  # ChatModelId & ConnectionString come from env vars


async def bootstrap():
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        kernel = Kernel()  # with your functions loaded
        agent: AzureAIAgent = await AgentRegistry.create_agent_from_yaml(
            spec,
            kernel=kernel,
            client=client,
            settings=settings,
        )
        async for resp in agent.invoke(messages="What's the weather in Seoul?"):
            print(resp)


asyncio.run(bootstrap())
