# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING

from opentelemetry import trace

from semantic_kernel.agents.strategies.termination.termination_strategy import TerminationStrategy
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.contents.chat_history import ChatHistory

if TYPE_CHECKING:
    from semantic_kernel.agents.agent import Agent
    from semantic_kernel.contents.chat_message_content import ChatMessageContent


TERMINATE_KEYWORD = "yes"


class CustomTerminationStrategy(TerminationStrategy):
    maximum_iterations: int = 2
    chat_completion_service: AzureChatCompletion

    def __init__(self, **kwargs):
        chat_completion_service = AzureChatCompletion()
        super().__init__(chat_completion_service=chat_completion_service, **kwargs)

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
                if content:
                    chat_history.add_message(message)

            completion = await self.chat_completion_service.get_chat_message_content(
                chat_history,
                AzureChatPromptExecutionSettings(),
            )

            return TERMINATE_KEYWORD in completion.content.lower()

    def get_system_message(self) -> str:
        return f"""
You will be given a chat history where there will be one user, one writer, and {len(self.agents) - 1} reviewers.
The writer is responsible for creating content.
The reviewers are responsible for providing feedback and approving the content.
The chat history may be empty at the beginning.

Following are the names and descriptions of the participants in fullfilling the user's request:
{"\n".join(f"{agent.name}: {agent.description}" for agent in self.agents)}

The content is considered approved only when all the reviewers agree that the content is ready for publication.
The content is not approved when none of the reviewers have spoken yet.
All participants must at least have spoken once.

Determine if the content has been approved. If so, say "{TERMINATE_KEYWORD}".
Otherwise, say "no".
"""
