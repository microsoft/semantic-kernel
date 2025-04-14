# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
import sys

from dotenv import load_dotenv
from self_hosted_api_chat_completion import SelfHostedChatCompletion

from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.strategies.termination.termination_strategy import TerminationStrategy
from semantic_kernel.contents import ChatMessageContent, AuthorRole
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel import Kernel

load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

#####################################################################
# The following sample demonstrates how to create a self-hosted.....#
# and have them participate in a group chat to work towards   ......#
# the user's requirement.                                           #
#####################################################################


class ApprovalTerminationStrategy(TerminationStrategy):
    """A strategy for determining when an agent should terminate."""

    async def should_agent_terminate(self, agent, history):
        """Check if the agent should terminate."""
        return "approved" in history[-1].content.lower()


REVIEWER_NAME = "ArtDirector"
COPYWRITER_NAME = "CopyWriter"


async def main():
    try:
        kernel = Kernel()

        agent_reviewer = ChatCompletionAgent(
            id="artdirector",
            kernel=kernel,
            name=REVIEWER_NAME,
            service=SelfHostedChatCompletion(url=os.getenv("REVIEWER_AGENT_URL") or "", ai_model_id=REVIEWER_NAME),
        )

        agent_writer = ChatCompletionAgent(
            id="copywriter",
            kernel=kernel,
            name=COPYWRITER_NAME,
            service=SelfHostedChatCompletion(url=os.getenv("COPYWRITER_AGENT_URL") or "", ai_model_id=COPYWRITER_NAME),
        )

        chat = AgentGroupChat(
            agents=[agent_writer, agent_reviewer],
            termination_strategy=ApprovalTerminationStrategy(agents=[agent_reviewer], maximum_iterations=10),
        )

        input = "a slogan for a new line of electric cars."

        await chat.add_chat_message(ChatMessageContent(role=AuthorRole.USER, content=input))
        print(f"# {AuthorRole.USER}: '{input}'")

        async for content in chat.invoke():
            print(f"# {content.role} - {content.name or '*'}: '{content.content}'")

        print(f"# IS COMPLETE: {chat.is_complete}")
    except Exception as e:
        print(e)


if __name__ == "__main__":
    asyncio.run(main())
