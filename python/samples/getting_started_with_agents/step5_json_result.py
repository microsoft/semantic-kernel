# Copyright (c) Microsoft. All rights reserved.

import asyncio

from pydantic import ValidationError

from semantic_kernel.agents import AgentGroupChat, ChatCompletionAgent
from semantic_kernel.agents.strategies.termination.termination_strategy import TerminationStrategy
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel import Kernel
from semantic_kernel.kernel_pydantic import KernelBaseModel

###################################################################
# The following sample demonstrates how to configure an Agent     #
# Group Chat, and invoke an agent with only a single turn.        #
# A custom termination strategy is provided where the model is    #
# to rate the user input on creativity and expressiveness         #
# and end the chat when a score of 70 or higher is provided.      #
###################################################################


SCORE_COMPLETED_THRESHOLD = 70
TUTOR_NAME = "Tutor"
TUTOR_INSTRUCTIONS = """
Think step-by-step and rate the user input on creativity and expressivness from 1-100.

Respond in JSON format with the following JSON schema:

{
    "score": "integer (1-100)",
    "notes": "the reason for your score"
}
"""


class InputScore(KernelBaseModel):
    """A model for the input score."""

    score: int
    notes: str


def translate_json(json_string: str) -> InputScore | None:
    try:
        if json_string is None:
            return None
        return InputScore.model_validate_json(json_string)
    except ValidationError:
        return None


class ThresholdTerminationStrategy(TerminationStrategy):
    """A strategy for determining when an agent should terminate."""

    async def should_agent_terminate(self, agent, history):
        """Check if the agent should terminate."""
        last_message_content = history[-1].content or ""
        result = translate_json(last_message_content)
        return result.score >= SCORE_COMPLETED_THRESHOLD if result else False


def _create_kernel_with_chat_completion(service_id: str) -> Kernel:
    kernel = Kernel()
    kernel.add_service(AzureChatCompletion(service_id=service_id))
    return kernel


async def invoke_agent(agent: ChatCompletionAgent, input: str, chat: AgentGroupChat):
    """Invoke the agent with the user input."""
    await chat.add_chat_message(ChatMessageContent(role=AuthorRole.USER, content=input))

    print(f"# {AuthorRole.USER}: '{input}'")

    async for content in chat.invoke_single_turn(agent):
        print(f"# {content.role} - {content.name or '*'}: '{content.content}'")
        print(f"# IS COMPLETE: {chat.is_complete}")


async def main():
    service_id = "tutor"
    agent = ChatCompletionAgent(
        service_id=service_id,
        kernel=_create_kernel_with_chat_completion(service_id=service_id),
        name=TUTOR_NAME,
        instructions=TUTOR_INSTRUCTIONS,
    )

    # Here a TerminationStrategy subclass is used that will terminate when
    # the response includes a score that is greater than or equal to 70.
    termination_strategy = ThresholdTerminationStrategy(maximum_iterations=10)

    chat = AgentGroupChat(termination_strategy=termination_strategy)

    await invoke_agent(agent=agent, input="The sunset is very colorful.", chat=chat)
    await invoke_agent(agent=agent, input="The sunset is setting over the mountains.", chat=chat)
    await invoke_agent(
        agent=agent,
        input="The sunset is setting over the mountains and filled the sky with a deep red flame, setting the clouds ablaze.",  # noqa: E501
        chat=chat,
    )


if __name__ == "__main__":
    asyncio.run(main())
