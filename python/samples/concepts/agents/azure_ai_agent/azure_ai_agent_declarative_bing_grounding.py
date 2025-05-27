# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AgentRegistry, AzureAIAgent, AzureAIAgentSettings

"""
The following sample demonstrates how to create an Azure AI agent that answers
user questions using the Bing Grounding tool.

The agent is created using a YAML declarative spec that configures the
Bing Grounding tool. The agent is then used to answer user questions
that require web search to answer correctly.

Note: the `BingConnectionId` is in the format of:
/subscriptions/<sub_id>/resourceGroups/<rg>/providers/Microsoft.MachineLearningServices/workspaces/<workspace>/connections/<bing_connection_id>

It can either be configured as an env var `AZURE_AI_AGENT_BING_CONNECTION_ID` or passed in as an extra to 
`create_from_yaml`: extras={"BingConnectionId": "<bing_connection_id>"}
"""

# Define the YAML string for the sample
spec = """
type: foundry_agent
name: BingAgent
instructions: Answer questions using Bing to provide grounding context.
description: This agent answers questions using Bing to provide grounding context.
model:
  id: ${AzureAI:ChatModelId}
  options:
    temperature: 0.4
tools:
  - type: bing_grounding
    options:
      tool_connections:
        - ${AzureAI:BingConnectionId}
"""

settings = AzureAIAgentSettings()  # ChatModelId & BingConnectionId come from .env/env vars


async def main():
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        try:
            # Create the AzureAI Agent from the YAML spec
            agent: AzureAIAgent = await AgentRegistry.create_from_yaml(
                yaml_str=spec,
                client=client,
                settings=settings,
            )

            # Define the task for the agent
            TASK = "Who won the 2025 NCAA basketball championship?"

            print(f"# User: '{TASK}'")

            # Invoke the agent for the specified task
            async for response in agent.invoke(
                messages=TASK,
            ):
                print(f"# {response.name}: {response}")
        finally:
            # Cleanup: Delete the thread and agent
            await client.agents.delete_agent(agent.id)

        """
        Sample output:

        # User: 'Who won the 2025 NCAA basketball championship?'
        # BingAgent: The Florida Gators won the 2025 NCAA men's basketball championship, narrowly defeating the Houston 
            Cougars 65-63 in the final game. This marked Florida's first national title since 
            2007【3:5†source】【3:9†source】.
        """


if __name__ == "__main__":
    asyncio.run(main())
