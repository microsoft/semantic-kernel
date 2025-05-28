# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents import AgentRegistry, OpenAIResponsesAgent

"""
The following sample demonstrates how to create an OpenAI Responses Agent that invokes
a story generation task using a prompt template and a declarative spec.
"""

# Define the YAML string for the sample
spec = """
type: openai_responses
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
    # Setup the OpenAI client
    client = OpenAIResponsesAgent.create_client()

    # Create the Responses Agent from the YAML spec
    # Note: the extras can be provided in the short-format (shown below) or
    # in the long-format (as shown in the YAML spec, with the `OpenAI:` prefix).
    # The short-format is used here for brevity
    agent: OpenAIResponsesAgent = await AgentRegistry.create_from_yaml(
        yaml_str=spec,
        client=client,
    )

    USER_INPUTS = ["Tell me a fun story."]

    # Invoke the agent for the specified task
    for user_input in USER_INPUTS:
        # Print the user input
        print(f"# User: '{user_input}'")
        # Invoke the agent for the specified task
        async for response in agent.invoke(
            messages=user_input,
        ):
            print(f"# {response.name}: {response}")

    """
    Sample output:

    # User: 'Tell me a fun story.'
    # StoryAgent: Late at night, a mischievous cat named Whiskers tiptoed across the piano keys, 
      accidentally composing a tune so catchy that all the neighborhood felines gathered outside 
      to dance. By morning, the humans awoke to find a crowd of cats meowing for an encore performance.
    """


if __name__ == "__main__":
    asyncio.run(main())
