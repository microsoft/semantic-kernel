# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents import CopilotStudioAgent, CopilotStudioAgentThread
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.functions import KernelArguments
from semantic_kernel.prompt_template import PromptTemplateConfig

"""
This sample demonstrates how to use the Copilot Studio agent to answer questions from the user.
It demonstrates how to use a thread to maintain context between user inputs.
It also demonstrates how to use a custom prompt template.
"""


async def main() -> None:
    # 1. Create the agent
    agent = CopilotStudioAgent(
        name="JokeAgent",
        instructions="You are a joker. Tell kid-friendly jokes.",
        prompt_template_config=PromptTemplateConfig(template="Craft jokes about {{$topic}}"),
    )

    # 2. Create a list of user inputs
    USER_INPUTS = [ChatMessageContent(role="user", content="Tell me a joke to make me laugh.")]

    # 3. Create a thread to maintain context between user inputs
    thread: CopilotStudioAgentThread | None = None

    # 4. Loop through the user inputs and get responses from the agent
    for user_input in USER_INPUTS:
        print(f"# User: {user_input}")
        response = await agent.get_response(
            messages=user_input, thread=thread, arguments=KernelArguments(topic="pirate")
        )
        print(f"# {response.name}: {response}")
        thread = response.thread

    # 5. If a thread was created, delete it when done
    if thread:
        await thread.delete()

    """
    # User: Tell me a joke to make me laugh.
    # JokeAgent: Sure, here are a few pirate jokes for you:

    1. Why don't pirates shower before they walk the plank?
    Because they'll just wash up on shore later!

    2. How do pirates prefer to communicate?
    Aye to aye!

    3. What's a pirate's favorite letter?
    You might think it's "R," but their true love is the "C"!

    Hope these made you smile!
    """


if __name__ == "__main__":
    asyncio.run(main())
