# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging

from semantic_kernel import Kernel
from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.strategies import TerminationStrategy
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

"""
The following sample demonstrates how to create a simple, agent group chat that
utilizes An Art Director Chat Completion Agent along with a Copy Writer Chat
Completion Agent to complete a task. The main point of this sample is to note
how to enable logging to view all interactions between the agents and the model.

Note: This sample use the `AgentGroupChat` feature of Semantic Kernel, which is
no longer maintained. For a replacement, consider using the `GroupChatOrchestration`.

Read more about the `GroupChatOrchestration` here:
https://learn.microsoft.com/semantic-kernel/frameworks/agent/agent-orchestration/group-chat?pivots=programming-language-python

Here is a migration guide from `AgentGroupChat` to `GroupChatOrchestration`:
https://learn.microsoft.com/semantic-kernel/support/migration/group-chat-orchestration-migration-guide?pivots=programming-language-python
"""

# 0. Enable logging
# NOTE: This is all that is required to enable logging.
# Set the desired level to INFO, DEBUG, etc.
logging.basicConfig(level=logging.INFO)


class ApprovalTerminationStrategy(TerminationStrategy):
    """A strategy for determining when an agent should terminate."""

    async def should_agent_terminate(self, agent, history):
        """Check if the agent should terminate."""
        return "approved" in history[-1].content.lower()


def _create_kernel_with_chat_completion(service_id: str) -> Kernel:
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(service_id=service_id))
    return kernel


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
        agents=[agent_writer, agent_reviewer],
        termination_strategy=ApprovalTerminationStrategy(agents=[agent_reviewer], maximum_iterations=10),
    )

    # 4. Add the task as a message to the group chat
    await group_chat.add_chat_message(message=TASK)
    print(f"# User: {TASK}")

    # 5. Invoke the chat
    async for content in group_chat.invoke():
        print(f"# {content.name}: {content.content}")

    """
    Sample output:
    INFO:semantic_kernel.agents.group_chat.agent_chat:Adding `1` agent chat messages
    # User: a slogan for a new line of electric cars.
    INFO:semantic_kernel.agents.strategies.selection.sequential_selection_strategy:Selected agent at index 0 (ID: ...
    INFO:semantic_kernel.agents.group_chat.agent_chat:Invoking agent CopyWriter
    INFO:semantic_kernel.utils.telemetry.model_diagnostics.decorators:{"role": "system", "content": "\nYou are a ...
    INFO:semantic_kernel.utils.telemetry.model_diagnostics.decorators:{"role": "user", "content": "a slogan for ...
    INFO:semantic_kernel.connectors.ai.open_ai.services.open_ai_handler:OpenAI usage: CompletionUsage(completion_...
    INFO:semantic_kernel.utils.telemetry.model_diagnostics.decorators:{"message": {"role": "assistant", "content": ...
    INFO:semantic_kernel.agents.chat_completion.chat_completion_agent:[ChatCompletionAgent] Invoked AzureChatCompl...
    INFO:semantic_kernel.agents.strategies.termination.termination_strategy:Evaluating termination criteria for ...
    INFO:semantic_kernel.agents.strategies.termination.termination_strategy:Agent 598d827e-ce5e-44fa-879b-42793bb...
    # CopyWriter: "Drive Change. Literally."
    INFO:semantic_kernel.agents.strategies.selection.sequential_selection_strategy:Selected agent at index 1 (ID: ...
    INFO:semantic_kernel.agents.group_chat.agent_chat:Invoking agent ArtDirector
    INFO:semantic_kernel.utils.telemetry.model_diagnostics.decorators:{"role": "system", "content": "\nYou are an ...
    INFO:semantic_kernel.utils.telemetry.model_diagnostics.decorators:{"role": "user", "content": "a slogan for a ...
    INFO:semantic_kernel.utils.telemetry.model_diagnostics.decorators:{"role": "assistant", "content": "\"Drive ...
    ...
    """


if __name__ == "__main__":
    asyncio.run(main())
