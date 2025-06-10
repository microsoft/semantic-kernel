# Copyright (c) Microsoft. All rights reserved.

import asyncio

from pydantic import BaseModel, ValidationError

from semantic_kernel import Kernel
from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.strategies import TerminationStrategy
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAIChatPromptExecutionSettings
from semantic_kernel.functions import KernelArguments

"""
The following sample demonstrates how to configure an Agent Group Chat, and invoke an
agent with only a single turn.A custom termination strategy is provided where the model
is to rate the user input on creativity and expressiveness and end the chat when a score
of 70 or higher is provided.

Note: This sample use the `AgentGroupChat` feature of Semantic Kernel, which is
no longer maintained. For a replacement, consider using the `GroupChatOrchestration`.

Read more about the `GroupChatOrchestration` here:
https://learn.microsoft.com/semantic-kernel/frameworks/agent/agent-orchestration/group-chat?pivots=programming-language-python

Here is a migration guide from `AgentGroupChat` to `GroupChatOrchestration`:
https://learn.microsoft.com/semantic-kernel/support/migration/group-chat-orchestration-migration-guide?pivots=programming-language-python
"""


def _create_kernel_with_chat_completion(service_id: str) -> Kernel:
    kernel = Kernel()
    kernel.add_service(OpenAIChatCompletion(service_id=service_id))
    return kernel


class InputScore(BaseModel):
    """A model for the input score."""

    score: int
    notes: str


class ThresholdTerminationStrategy(TerminationStrategy):
    """A strategy for determining when an agent should terminate."""

    threshold: int = 70

    async def should_agent_terminate(self, agent, history):
        """Check if the agent should terminate."""
        try:
            result = InputScore.model_validate_json(history[-1].content or "")
            return result.score >= self.threshold
        except ValidationError:
            return False


INSTRUCTION = """
Think step-by-step and rate the user input on creativity and expressiveness from 1-100 with some notes on improvements.
"""

# Simulate a conversation with the agent
USER_INPUTS = {
    "The sunset is very colorful.",
    "The sunset is setting over the mountains.",
    "The sunset is setting over the mountains and fills the sky with a deep red flame, setting the clouds ablaze.",
}


async def main():
    # 1. Create the instance of the Kernel to register a service
    service_id = "agent"
    kernel = _create_kernel_with_chat_completion(service_id)

    # 2. Configure the prompt execution settings to return the score in the desired format
    settings = kernel.get_prompt_execution_settings_from_service_id(service_id)
    assert isinstance(settings, OpenAIChatPromptExecutionSettings)  # nosec
    settings.response_format = InputScore

    # 3. Create the agent
    agent = ChatCompletionAgent(
        kernel=kernel,
        name="Tutor",
        instructions=INSTRUCTION,
        arguments=KernelArguments(settings),
    )

    # 4. Create the group chat with the custom termination strategy
    group_chat = AgentGroupChat(termination_strategy=ThresholdTerminationStrategy(maximum_iterations=10))

    for user_input in USER_INPUTS:
        # 5. Add the user input to the chat history
        await group_chat.add_chat_message(message=user_input)
        print(f"# User: {user_input}")

        # 6. Invoke the chat with the agent for a response
        async for content in group_chat.invoke_single_turn(agent):
            print(f"# {content.name}: {content.content}")

    """
    Sample output:
    # User: The sunset is very colorful.
    # Tutor: {"score":45,"notes":"The sentence 'The sunset is very colorful' is simple and direct. While it ..."}
    # User: The sunset is setting over the mountains.
    # Tutor: {"score":50,"notes":"This sentence provides a basic scene of a sunset over mountains, which ..."}
    # User: The sunset is setting over the mountains and fills the sky with a deep red flame, setting the clouds ablaze.
    # Tutor: {"score":75,"notes":"This sentence demonstrates improved creativity and expressiveness by ..."}
    """


if __name__ == "__main__":
    asyncio.run(main())
