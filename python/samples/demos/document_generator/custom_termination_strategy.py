# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING, ClassVar

from opentelemetry import trace
from pydantic import Field

from semantic_kernel.agents.strategies import TerminationStrategy
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatPromptExecutionSettings,
    OpenAIChatCompletion,
)
from semantic_kernel.contents import ChatHistory

if TYPE_CHECKING:
    from semantic_kernel.agents.agent import Agent
    from semantic_kernel.contents.chat_message_content import ChatMessageContent


TERMINATE_TRUE_KEYWORD = "yes"
TERMINATE_FALSE_KEYWORD = "no"

NEWLINE = "\n"


class CustomTerminationStrategy(TerminationStrategy):
    NUM_OF_RETRIES: ClassVar[int] = 3

    maximum_iterations: int = 20
    chat_completion_service: ChatCompletionClientBase = Field(default_factory=lambda: OpenAIChatCompletion())

    async def should_agent_terminate(self, agent: "Agent", history: list["ChatMessageContent"]) -> bool:
        """Check if the agent should terminate.

        Args:
            agent: The agent to check.
            history: The history of messages in the conversation.
        """
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span("terminate_strategy"):
            chat_history = ChatHistory(system_message=self.get_system_message().strip())

            for message in history:
                content = message.content
                # We don't want to add messages whose text content is empty.
                # Those messages are likely messages from function calls and function results.
                if content:
                    chat_history.add_message(message)

            chat_history.add_user_message(
                "Is the latest content approved by all agents? "
                f"Answer with '{TERMINATE_TRUE_KEYWORD}' or '{TERMINATE_FALSE_KEYWORD}'."
            )

            for _ in range(self.NUM_OF_RETRIES):
                completion = await self.chat_completion_service.get_chat_message_content(
                    chat_history,
                    AzureChatPromptExecutionSettings(),
                )

                if not completion:
                    continue

                if TERMINATE_FALSE_KEYWORD in completion.content.lower():
                    return False
                if TERMINATE_TRUE_KEYWORD in completion.content.lower():
                    return True

                chat_history.add_message(completion)
                chat_history.add_user_message(
                    f"You must only say either '{TERMINATE_TRUE_KEYWORD}' or '{TERMINATE_FALSE_KEYWORD}'."
                )

            raise ValueError(
                "Failed to determine if the agent should terminate because the model did not return a valid response."
            )

    def get_system_message(self) -> str:
        return f"""
You are in a chat with multiple agents collaborating to create a document.
Each message in the chat history contains the agent's name and the message content.

The chat history may start empty as no agents have spoken yet.

Here are the agents with their indices, names, and descriptions:
{NEWLINE.join(f"[{index}] {agent.name}:{NEWLINE}{agent.description}" for index, agent in enumerate(self.agents))}

Your task is NOT to continue the conversation. Determine if the latest content is approved by all agents.
If approved, say "{TERMINATE_TRUE_KEYWORD}". Otherwise, say "{TERMINATE_FALSE_KEYWORD}".
"""
