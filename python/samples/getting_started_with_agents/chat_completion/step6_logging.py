# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging

from semantic_kernel import Kernel
from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.strategies import TerminationStrategy
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import AuthorRole, ChatMessageContent

###################################################################
# The following sample demonstrates how to create a simple,       #
# agent group chat that utilizes An Art Director Chat Completion  #
# Agent along with a Copy Writer Chat Completion Agent to         #
# complete a task. The main point of this sample is to note how   #
# to enable logging to view all interactions between the agents   #
# and the model.                                                  #
###################################################################


# NOTE: This is all that is required to enable logging
logging.basicConfig(level=logging.DEBUG)


class ApprovalTerminationStrategy(TerminationStrategy):
    """A strategy for determining when an agent should terminate."""

    async def should_agent_terminate(self, agent, history):
        """Check if the agent should terminate."""
        return "approved" in history[-1].content.lower()


def _create_kernel_with_chat_completion(service_id: str) -> Kernel:
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(service_id=service_id))
    return kernel


async def main():
    REVIEWER_NAME = "ArtDirector"
    REVIEWER_INSTRUCTIONS = """
    You are an art director who has opinions about copywriting born of a love for David Ogilvy.
    The goal is to determine if the given copy is acceptable to print.
    If so, state that it is approved.
    If not, provide insight on how to refine suggested copy without example.
    """
    agent_reviewer = ChatCompletionAgent(
        service_id="artdirector",
        kernel=_create_kernel_with_chat_completion("artdirector"),
        name=REVIEWER_NAME,
        instructions=REVIEWER_INSTRUCTIONS,
    )

    COPYWRITER_NAME = "CopyWriter"
    COPYWRITER_INSTRUCTIONS = """
    You are a copywriter with ten years of experience and are known for brevity and a dry humor.
    The goal is to refine and decide on the single best copy as an expert in the field.
    Only provide a single proposal per response.
    You're laser focused on the goal at hand.
    Don't waste time with chit chat.
    Consider suggestions when refining an idea.
    """
    agent_writer = ChatCompletionAgent(
        service_id="copywriter",
        kernel=_create_kernel_with_chat_completion("copywriter"),
        name=COPYWRITER_NAME,
        instructions=COPYWRITER_INSTRUCTIONS,
    )

    group_chat = AgentGroupChat(
        agents=[agent_writer, agent_reviewer],
        termination_strategy=ApprovalTerminationStrategy(agents=[agent_reviewer], maximum_iterations=10),
    )

    input = "a slogan for a new line of electric cars."

    await group_chat.add_chat_message(ChatMessageContent(role=AuthorRole.USER, content=input))
    print(f"# User: '{input}'")

    async for content in group_chat.invoke():
        print(f"# Agent - {content.name or '*'}: '{content.content}'")

    print(f"# IS COMPLETE: {group_chat.is_complete}")


if __name__ == "__main__":
    asyncio.run(main())
