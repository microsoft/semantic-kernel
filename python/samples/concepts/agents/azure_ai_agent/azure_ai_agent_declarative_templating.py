# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import AgentRegistry, AzureAIAgent

"""
The following sample demonstrates how to create an Azure AI Agent that invokes
a story generation task using a prompt template and a declarative spec.
"""

# Define the YAML string for the sample
spec = """
type: foundry_agent
name: StoryAgent
description: An agent that generates a story about a topic.
instructions: Tell a story about {{$topic}} that is {{$length}} sentences long.
model:
  id: ${AzureAI:ChatModelId}
  connection:
    connection_string: ${AzureAI:Endpoint}
inputs:
  topic:
    description: The topic of the story.
    required: true
    default: Cats
  length:
    description: The number of sentences in the story.
    required: true
    default: 2
outputs:
  output1:
    description: The generated story.
template:
  format: semantic-kernel
"""


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
            )

            # Invoke the agent for the specified task
            async for response in agent.invoke(
                messages=None,
            ):
                print(f"# {response.name}: {response}")
        finally:
            # Cleanup: Delete the agent, vector store, and file
            await client.agents.delete_agent(agent.id)

    """
    Sample output:

    # StoryAgent: Under the silvery moon, three mischievous cats tiptoed across the rooftop, chasing 
      shadows and sharing secret whispers. By dawn, they curled up together, purring softly, dreaming 
      of adventures yet to come.
    """


if __name__ == "__main__":
    asyncio.run(main())
