# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING, ClassVar

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


TERMINATE_TRUE_KEYWORD = "yes"
TERMINATE_FALSE_KEYWORD = "no"


class CustomTerminationStrategy(TerminationStrategy):
    NUM_OF_RETRIES: ClassVar[int] = 3

    maximum_iterations: int = 20
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
                # We don't want to add messages whose text content is empty.
                # Those messages are likely messages from function calls and function results.
                if content:
                    chat_history.add_message(message)

            for _ in range(self.NUM_OF_RETRIES):
                completion = await self.chat_completion_service.get_chat_message_content(
                    chat_history,
                    AzureChatPromptExecutionSettings(),
                )

                if TERMINATE_FALSE_KEYWORD in completion.content.lower():
                    return False
                if TERMINATE_TRUE_KEYWORD in completion.content.lower():
                    return True

                chat_history.add_message(completion)
                chat_history.add_user_message_str(
                    f"You must only say either '{TERMINATE_TRUE_KEYWORD}' or '{TERMINATE_FALSE_KEYWORD}'."
                )

            raise ValueError(
                "Failed to determine if the agent should terminate because the model did not return a valid response."
            )

    def get_system_message(self) -> str:
        return f"""
You are in a chat where multiple agents are involved in creating a document.

The chat history may be empty at the beginning as none of the agents have spoken yet.

Following are the names and introductions of the agents in fullfilling the user's request:
{"\n".join(f"{agent.name}: {agent.description}" for agent in self.agents)}

The content is considered approved only when all the reviewers have agreed and validated that the content is
ready for publication.
Whenever the writer updates the document, the reviewers must reapprove and revalidate the content.
All agents must at least have spoken once.

Your job is NOT to continue the conversation, but to determine if the content has been approved based on the chat.
If so, say "{TERMINATE_TRUE_KEYWORD}". Otherwise, say "{TERMINATE_FALSE_KEYWORD}".
"""
