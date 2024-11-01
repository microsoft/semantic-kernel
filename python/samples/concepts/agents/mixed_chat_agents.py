# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.open_ai import OpenAIAssistantAgent
from semantic_kernel.agents.strategies.termination.termination_strategy import TerminationStrategy
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel import Kernel

#####################################################################
# The following sample demonstrates how to create an OpenAI         #
# assistant using either Azure OpenAI or OpenAI, a chat completion  #
# agent and have them participate in a group chat to work towards   #
# the user's requirement.                                           #
#####################################################################


class ApprovalTerminationStrategy(TerminationStrategy):
    """A strategy for determining when an agent should terminate."""

    async def should_agent_terminate(self, agent, history):
        """Check if the agent should terminate."""
        return "approved" in history[-1].content.lower()


REVIEWER_NAME = "ArtDirector"
REVIEWER_INSTRUCTIONS = """
You are an art director who has opinions about copywriting born of a love for David Ogilvy.
The goal is to determine if the given copy is acceptable to print.
If so, state that it is approved. Only include the word "approved" if it is so.
If not, provide insight on how to refine suggested copy without example.
"""

COPYWRITER_NAME = "CopyWriter"
COPYWRITER_INSTRUCTIONS = """
You are a copywriter with ten years of experience and are known for brevity and a dry humor.
The goal is to refine and decide on the single best copy as an expert in the field.
Only provide a single proposal per response.
You're laser focused on the goal at hand.
Don't waste time with chit chat.
Consider suggestions when refining an idea.
"""


def _create_kernel_with_chat_completion(service_id: str) -> Kernel:
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(service_id=service_id))
    return kernel


async def main():
    try:
        agent_reviewer = ChatCompletionAgent(
            service_id="artdirector",
            kernel=_create_kernel_with_chat_completion("artdirector"),
            name=REVIEWER_NAME,
            instructions=REVIEWER_INSTRUCTIONS,
        )

        agent_writer = await OpenAIAssistantAgent.create(
            service_id="copywriter",
            kernel=Kernel(),
            name=COPYWRITER_NAME,
            instructions=COPYWRITER_INSTRUCTIONS,
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
    finally:
        await agent_writer.delete()


if __name__ == "__main__":
    asyncio.run(main())
