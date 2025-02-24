# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from autogen import ConversableAgent

from semantic_kernel.agents.autogen.autogen_conversable_agent import AutoGenConversableAgent

"""
The following sample demonstrates how to use the AutoGenConversableAgent to create a conversation between two agents
where one agent suggests a joke and the other agent generates a joke.

The sample follows the AutoGen flow outlined here:
https://microsoft.github.io/autogen/0.2/docs/tutorial/introduction#roles-and-conversations
"""


async def main():
    cathy = ConversableAgent(
        "cathy",
        system_message="Your name is Cathy and you are a part of a duo of comedians.",
        llm_config={
            "config_list": [
                {
                    "model": os.environ["OPENAI_CHAT_MODEL_ID"],
                    "temperature": 0.9,
                    "api_key": os.environ.get("OPENAI_API_KEY"),
                }
            ]
        },
        human_input_mode="NEVER",  # Never ask for human input.
    )

    cathy_autogen_agent = AutoGenConversableAgent(conversable_agent=cathy)

    joe = ConversableAgent(
        "joe",
        system_message="Your name is Joe and you are a part of a duo of comedians.",
        llm_config={
            "config_list": [
                {
                    "model": os.environ["OPENAI_CHAT_MODEL_ID"],
                    "temperature": 0.7,
                    "api_key": os.environ.get("OPENAI_API_KEY"),
                }
            ]
        },
        human_input_mode="NEVER",  # Never ask for human input.
    )

    joe_autogen_agent = AutoGenConversableAgent(conversable_agent=joe)

    async for content in cathy_autogen_agent.invoke(
        recipient=joe_autogen_agent, message="Tell me a joke about the stock market.", max_turns=3
    ):
        print(f"# {content.role} - {content.name or '*'}: '{content.content}'")


if __name__ == "__main__":
    asyncio.run(main())
