# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents import CopilotStudioAgent, CopilotStudioAgentThread

"""
This sample demonstrates how to use the Copilot Studio agent to perform a web search.
In Copilot Studio, for the specified agent, you must enable the "Web Search" capability.
If not already enabled, make sure to (re-)publish the agent so the changes take effect.
"""


async def main() -> None:
    # 1. Create the agent
    agent = CopilotStudioAgent(
        name="WebSearchAgent",
        instructions="Help answer the user's questions by searching the web.",
    )

    # 2. Create a list of user inputs
    USER_INPUTS = [
        "Which team won the 2025 NCAA Basketball championship?",
    ]

    # 3. Create a thread to maintain context between user inputs
    thread: CopilotStudioAgentThread | None = None

    # 4. Loop through the user inputs and get responses from the agent
    for user_input in USER_INPUTS:
        print(f"# User: {user_input}")
        async for response in agent.invoke(messages=user_input, thread=thread):
            print(f"# {response.name}: {response}")
            thread = response.thread

    # 5. If a thread was created, delete it when done
    if thread:
        await thread.delete()
    """
    Sample output:

    # User: Which team won the 2025 NCAA Basketball championship?
    # WebSearchAgent: The Florida Gators won the 2025 NCAA Basketball championship by defeating the Houston Cougars 
        with a score of 65-63 [1].

    [1]: https://www.ncaa.com/news/basketball-men/mml-official-bracket/2025-04-06/latest-bracket-schedule-and-scores-2025-ncaa-mens-tournament 
    "Latest bracket, schedule and scores for the 2025 NCAA men's tournament"
    """


if __name__ == "__main__":
    asyncio.run(main())
