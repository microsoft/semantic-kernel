# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents import AgentGroupChat, BedrockAgent, ChatCompletionAgent
from semantic_kernel.agents.strategies.termination.termination_strategy import TerminationStrategy
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel import Kernel

"""
This sample shows how to use a bedrock agent in a group chat that includes multiple agents of different roles.
This sample uses the following main component(s):
- a Bedrock agent
- a ChatCompletionAgent
- an AgentGroupChat
You will learn how to create a new or connect to an existing Bedrock agent and put it in a group chat with
another agent.

Note: This sample use the `AgentGroupChat` feature of Semantic Kernel, which is
no longer maintained. For a replacement, consider using the `GroupChatOrchestration`.

Read more about the `GroupChatOrchestration` here:
https://learn.microsoft.com/semantic-kernel/frameworks/agent/agent-orchestration/group-chat?pivots=programming-language-python

Here is a migration guide from `AgentGroupChat` to `GroupChatOrchestration`:
https://learn.microsoft.com/semantic-kernel/support/migration/group-chat-orchestration-migration-guide?pivots=programming-language-python
"""

# This will be a chat completion agent
REVIEWER_NAME = "ArtDirector"
REVIEWER_INSTRUCTIONS = """
You are an art director who has opinions about copywriting born of a love for David Ogilvy.
The goal is to determine if the given copy is acceptable to print.
If so, state that it is approved. Only include the word "approved" if it is so.
If not, provide insight on how to refine suggested copy without example.
"""

# This will be a bedrock agent
COPYWRITER_NAME = "CopyWriter"
COPYWRITER_INSTRUCTIONS = """
You are a copywriter with ten years of experience and are known for brevity and a dry humor.
The goal is to refine and decide on the single best copy as an expert in the field.
Only provide a single proposal per response.
You're laser focused on the goal at hand.
Don't waste time with chit chat.
Consider suggestions when refining an idea.
"""


class ApprovalTerminationStrategy(TerminationStrategy):
    """A strategy for determining when an agent should terminate."""

    async def should_agent_terminate(self, agent, history):
        """Check if the agent should terminate."""
        return "approved" in history[-1].content.lower()


def _create_kernel_with_chat_completion() -> Kernel:
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion())
    return kernel


async def main():
    agent_reviewer = ChatCompletionAgent(
        kernel=_create_kernel_with_chat_completion(),
        name=REVIEWER_NAME,
        instructions=REVIEWER_INSTRUCTIONS,
    )

    agent_writer = await BedrockAgent.create_and_prepare_agent(
        COPYWRITER_NAME,
        instructions=COPYWRITER_INSTRUCTIONS,
    )

    chat = AgentGroupChat(
        agents=[agent_writer, agent_reviewer],
        termination_strategy=ApprovalTerminationStrategy(
            agents=[agent_reviewer],
            maximum_iterations=10,
        ),
    )

    input = "A slogan for a new line of electric cars."

    await chat.add_chat_message(message=input)
    print(f"# {AuthorRole.USER}: '{input}'")

    try:
        current_agent = "*"
        async for message_chunk in chat.invoke_stream():
            if current_agent != message_chunk.name:
                current_agent = message_chunk.name or "*"
                print(f"\n# {message_chunk.role} - {current_agent}: ", end="")
            print(message_chunk.content, end="")
        print()
        print(f"# IS COMPLETE: {chat.is_complete}")
    finally:
        # Delete the agent
        await agent_writer.delete_agent()

    # Sample output (using anthropic.claude-3-haiku-20240307-v1:0):
    # AuthorRole.USER: 'A slogan for a new line of electric cars.'
    # AuthorRole.ASSISTANT - CopyWriter: 'Charge Ahead: The Future of Driving'
    # AuthorRole.ASSISTANT - ArtDirector: 'The slogan "Charge Ahead: The Future of Driving" is compelling but could be
    # made even more impactful. Consider clarifying the unique selling proposition of the electric cars. Focus on what
    # sets them apart in terms of performance, eco-friendliness, or innovation. This will help create an emotional
    # connection and a clearer message for the audience.'
    # AuthorRole.ASSISTANT - CopyWriter: 'Charge Forward: The Electrifying Future of Driving'
    # AuthorRole.ASSISTANT - ArtDirector: 'Approved'
    # IS COMPLETE: True


if __name__ == "__main__":
    asyncio.run(main())
