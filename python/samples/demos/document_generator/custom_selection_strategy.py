# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING, ClassVar

from opentelemetry import trace

from semantic_kernel.agents.strategies.selection.selection_strategy import SelectionStrategy
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.agents import Agent
    from semantic_kernel.contents.chat_message_content import ChatMessageContent


@experimental_class
class CustomSelectionStrategy(SelectionStrategy):
    """A selection strategy that selects the next agent intelligently."""

    NUM_OF_RETRIES: ClassVar[int] = 3

    chat_completion_service: AzureChatCompletion

    def __init__(self, **kwargs):
        chat_completion_service = AzureChatCompletion()

        super().__init__(chat_completion_service=chat_completion_service, **kwargs)

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

            for _ in range(self.NUM_OF_RETRIES):
                completion = await self.chat_completion_service.get_chat_message_content(
                    chat_history,
                    AzureChatPromptExecutionSettings(),
                )

                try:
                    return agents[int(completion.content)]
                except ValueError as ex:
                    chat_history.add_message(completion)
                    chat_history.add_user_message_str(str(ex))

            raise ValueError("Failed to select an agent since the model did not return a valid index")

    def get_system_message(self, agents: list["Agent"]) -> str:
        return f"""
You are in a chat where multiple agents are involved in creating a document.

The chat history may be empty at the beginning as none of the agents have spoken yet.

Following are the indices, names and introductions of the agents in fullfilling the user's request:
{"\n".join(f"[{index}] {agent.name}:\n{agent.description}" for index, agent in enumerate(agents))}

Let the writer create the document first. Then let the reviewers will review and validate the content.
Once the writer updates the document, the reviewers must reapprove and revalidate the content.
If there is an agent that represents the user, only pick that agent when the other agents have given positive feedback.

Your job is NOT to continue the conversation, but to pick the most appropriate agents to speak next based on
the conversation history by its index. No agent should speak more than once in a row.

You response should be a number between 0 and {len(agents) - 1}.
Only return the index of the agent and nothing else. Your response should be parsaable as an integer.
"""
