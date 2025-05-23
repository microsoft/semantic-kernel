# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents import AgentRegistry, OpenAIResponsesAgent

"""
The following sample demonstrates how to create an OpenAI Responses Agent that answers
user questions using the web search tool based on a declarative spec.
"""

# Define the YAML string for the sample
spec = """
type: openai_responses
name: WebSearchAgent
description: Agent with web search tool.
instructions: >
  Find answers to the user's questions using the provided tool.
model:
  id: ${OpenAI:ChatModelId}
  connection:
    api_key: ${OpenAI:ApiKey}
tools:
  - type: web_search
    description: Search the internet for recent information.
    options:
      search_context_size: high
"""


async def main():
    # Setup the OpenAI client
    client = OpenAIResponsesAgent.create_client()

    try:
        # Create the Responses Agent from the YAML spec
        # Note: the extras can be provided in the short-format (shown below) or
        # in the long-format (as shown in the YAML spec, with the `OpenAI:` prefix).
        # The short-format is used here for brevity
        agent: OpenAIResponsesAgent = await AgentRegistry.create_from_yaml(
            yaml_str=spec,
            client=client,
        )

        # Define the task for the agent
        USER_INPUTS = ["Who won the 2025 NCAA basketball championship?"]

        thread = None

        for user_input in USER_INPUTS:
            # Print the user input
            print(f"# User: '{user_input}'")

            # Invoke the agent for the specified task
            async for response in agent.invoke(
                messages=user_input,
                thread=thread,
            ):
                print(f"# {response.name}: {response}")
                thread = response.thread
    finally:
        await thread.delete() if thread else None

    """
    Sample output:

    # User: 'Who won the 2025 NCAA basketball championship?'
    # WebSearchAgent: The Florida Gators won the 2025 NCAA men's basketball championship, defeating the Houston 
        Cougars 65-63 on April 7, 2025, at the Alamodome in San Antonio, Texas. This victory marked Florida's 
        third national title and their first since 2007. ([reuters.com](https://www.reuters.com/sports/basketball/florida-beat-houston-claim-third-ncaa-mens-basketball-title-2025-04-08/?utm_source=openai))

    In the championship game, Florida overcame a 12-point deficit in the second half. Senior guard Walter Clayton 
        Jr. was instrumental in the comeback, scoring all 11 of his points in the second half and delivering a 
        crucial defensive stop in the final seconds to secure the win. Will Richard led the Gators with 18 points. ([apnews.com](https://apnews.com/article/74a9c790277595ce53ca130c5ec64429?utm_source=openai))

    Head coach Todd Golden, in his third season, became the youngest coach to win the NCAA title since 1983. ([reuters.com](https://www.reuters.com/sports/basketball/florida-beat-houston-claim-third-ncaa-mens-basketball-title-2025-04-08/?utm_source=openai))

    ## Florida Gators' 2025 NCAA Championship Victory:
    - [Florida overcome Houston in massive comeback to claim third NCAA title](https://www.reuters.com/sports/basketball/florida-beat-houston-claim-third-ncaa-mens-basketball-title-2025-04-08/?utm_source=openai)
    - [Walter Clayton Jr.'s defensive stop gives Florida its 3rd national title with 65-63 win over Houston](https://apnews.com/article/74a9c790277595ce53ca130c5ec64429?utm_source=openai)
    - [Reports: National champion Florida sets White House visit](https://www.reuters.com/sports/reports-national-champion-florida-sets-white-house-visit-2025-05-18/?utm_source=openai) 
    """


if __name__ == "__main__":
    asyncio.run(main())
