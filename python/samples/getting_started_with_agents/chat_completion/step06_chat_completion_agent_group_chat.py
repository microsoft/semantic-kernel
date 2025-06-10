# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel import Kernel
from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.strategies import TerminationStrategy
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

"""
The following sample demonstrates how to create a simple, agent group chat that
utilizes An Art Director Chat Completion Agent along with a Copy Writer Chat
Completion Agent to complete a task.

Note: This sample use the `AgentGroupChat` feature of Semantic Kernel, which is
no longer maintained. For a replacement, consider using the `GroupChatOrchestration`.

Read more about the `GroupChatOrchestration` here:
https://learn.microsoft.com/semantic-kernel/frameworks/agent/agent-orchestration/group-chat?pivots=programming-language-python

Here is a migration guide from `AgentGroupChat` to `GroupChatOrchestration`:
https://learn.microsoft.com/semantic-kernel/support/migration/group-chat-orchestration-migration-guide?pivots=programming-language-python
"""


def _create_kernel_with_chat_completion(service_id: str) -> Kernel:
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(service_id=service_id))
    return kernel


class ApprovalTerminationStrategy(TerminationStrategy):
    """A strategy for determining when an agent should terminate."""

    async def should_agent_terminate(self, agent, history):
        """Check if the agent should terminate."""
        return "approved" in history[-1].content.lower()


REVIEWER_NAME = "ArtDirector"
REVIEWER_INSTRUCTIONS = """
You are an art director who has opinions about copywriting born of a love for David Ogilvy.
The goal is to determine if the given copy is acceptable to print.
If so, state that it is approved.
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

TASK = "a slogan for a new line of electric cars."


async def main():
    # 1. Create the reviewer agent based on the chat completion service
    agent_reviewer = ChatCompletionAgent(
        kernel=_create_kernel_with_chat_completion("artdirector"),
        name=REVIEWER_NAME,
        instructions=REVIEWER_INSTRUCTIONS,
    )

    # 2. Create the copywriter agent based on the chat completion service
    agent_writer = ChatCompletionAgent(
        kernel=_create_kernel_with_chat_completion("copywriter"),
        name=COPYWRITER_NAME,
        instructions=COPYWRITER_INSTRUCTIONS,
    )

    # 3. Place the agents in a group chat with a custom termination strategy
    group_chat = AgentGroupChat(
        agents=[
            agent_writer,
            agent_reviewer,
        ],
        termination_strategy=ApprovalTerminationStrategy(
            agents=[agent_reviewer],
            maximum_iterations=10,
        ),
    )

    # 4. Add the task as a message to the group chat
    await group_chat.add_chat_message(message=TASK)
    print(f"# User: {TASK}")

    # 5. Invoke the chat
    async for content in group_chat.invoke():
        print(f"# {content.name}: {content.content}")

    """
    Sample output:
    # User: a slogan for a new line of electric cars.
    # CopyWriter: "Drive the Future: Shockingly Efficient."
    # ArtDirector: This slogan has potential but could benefit from refinement to create a stronger ...
    # CopyWriter: "Electrify Your Drive."
    # ArtDirector: Approved. This slogan is concise, memorable, and effectively communicates the ...
    """


if __name__ == "__main__":
    asyncio.run(main())
