# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING, ClassVar

from opentelemetry import trace
from pydantic import Field

from semantic_kernel.agents.strategies.selection.selection_strategy import SelectionStrategy
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatPromptExecutionSettings,
    OpenAIChatCompletion,
)
from semantic_kernel.contents import ChatHistory
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from semantic_kernel.agents import Agent
    from semantic_kernel.contents.chat_message_content import ChatMessageContent

NEWLINE = "\n"


@experimental
class CustomSelectionStrategy(SelectionStrategy):
    """A selection strategy that selects the next agent intelligently."""

    NUM_OF_RETRIES: ClassVar[int] = 3

    chat_completion_service: ChatCompletionClientBase = Field(default_factory=lambda: OpenAIChatCompletion())

    async def next(self, agents: list["Agent"], history: list["ChatMessageContent"]) -> "Agent":
        """Select the next agent to interact with.

        Args:
            agents: The list of agents to select from.
            history: The history of messages in the conversation.

        Returns:
            The next agent to interact with.
        """
        if len(agents) == 0:
            raise ValueError("No agents to select from")

        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span("selection_strategy"):
            chat_history = ChatHistory(system_message=self.get_system_message(agents).strip())

            for message in history:
                content = message.content
                # We don't want to add messages whose text content is empty.
                # Those messages are likely messages from function calls and function results.
                if content:
                    chat_history.add_message(message)

            chat_history.add_user_message("Now follow the rules and select the next agent by typing the agent's index.")

            for _ in range(self.NUM_OF_RETRIES):
                completion = await self.chat_completion_service.get_chat_message_content(
                    chat_history,
                    AzureChatPromptExecutionSettings(),
                )

                if completion is None:
                    continue

                try:
                    return agents[int(completion.content)]
                except ValueError as ex:
                    chat_history.add_message(completion)
                    chat_history.add_user_message(str(ex))
                    chat_history.add_user_message(f"You must only say a number between 0 and {len(agents) - 1}.")

            raise ValueError("Failed to select an agent since the model did not return a valid index")

    def get_system_message(self, agents: list["Agent"]) -> str:
        return f"""
You are in a multi-agent chat to create a document.
Each message in the chat history contains the agent's name and the message content.

Initially, the chat history may be empty.

Here are the agents with their indices, names, and descriptions:
{NEWLINE.join(f"[{index}] {agent.name}:{NEWLINE}{agent.description}" for index, agent in enumerate(agents))}

Your task is to select the next agent based on the conversation history.

The conversation must follow these steps:
1. The content creation agent writes a draft.
2. The code validation agent checks the code in the draft.
3. The content creation agent updates the draft based on the feedback.
4. The code validation agent checks the updated code.
...
If the code validation agent approves the code, the user agent can ask the user for final feedback.
N: The user agent provides feedback. 
(If the feedback is not positive, the conversation goes back to the content creation agent.)

Respond with a single number between 0 and {len(agents) - 1}, representing the agent's index.
Only return the index as an integer.
"""
