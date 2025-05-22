# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents import OpenAIAssistantAgent
from semantic_kernel.agents.agent import AgentRegistry

"""
The following sample demonstrates how to create an OpenAI Assistant Agent that answers
user questions using the file search tool.

The agent is used to answer user questions that require file search to help ground 
answers from the model.
"""

# Define the YAML string for the sample
spec = """
type: openai_assistant
name: StoryAgent
description: An agent that generates a story about a topic.
instructions: Tell a story about {{$topic}} that is {{$length}} sentences long.
model:
  id: ${OpenAI:ChatModelId}
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
    # Setup the OpenAI Assistant client
    client = OpenAIAssistantAgent.create_client()

    try:
        # Create the Assistant Agent from the YAML spec
        # Note: the extras can be provided in the short-format (shown below) or
        # in the long-format (as shown in the YAML spec, with the `OpenAI:` prefix).
        # The short-format is used here for brevity
        agent: OpenAIAssistantAgent = await AgentRegistry.create_from_yaml(
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
        await client.beta.assistants.delete(agent.id)

        """
        Sample output:

        # User: 'Who can help me if I have a sales question?'
        # FileSearchAgent: If you have a sales question, you may contact the following individuals:

        1. **Hicran Bea** - Sales Manager
        2. **Mariam Jaslyn** - Sales Representative
        3. **Angelino Embla** - Sales Representative

        This information comes from the employee records【4:0†source】.
        """


if __name__ == "__main__":
    asyncio.run(main())
