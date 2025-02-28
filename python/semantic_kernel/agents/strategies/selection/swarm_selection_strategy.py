# Copyright (c) Microsoft. All rights reserved.

import logging
import sys

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from typing import TYPE_CHECKING

from semantic_kernel.agents import Agent
from semantic_kernel.agents.strategies.selection.selection_strategy import SelectionStrategy
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.exceptions.agent_exceptions import AgentChatException
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from semantic_kernel.contents.chat_message_content import ITEM_TYPES, ChatMessageContent


logger: logging.Logger = logging.getLogger(__name__)


@experimental
class SwarmSelectionStrategy(SelectionStrategy):
    """Swarm Agent Strategy, Agents are selected with FunctionCalls that return an Agent Type."""

    current_agent: Agent | None = None

    @override
    async def select_agent(
        self,
        agents: list["Agent"],
        history: list["ChatMessageContent"],
    ) -> "Agent":
        """Select the next agent in a swarm fashion.

        Args:
            agents: The list of agents to select from.
            history: The history of messages in the conversation.

        Returns:
            The agent who takes the next turn.
        """
        # If only user messages are in the history, return the first agent
        if len(history) <= 1:
            self.current_agent = agents[0]
            return agents[0]

        # Pick the agent from the last message if it was a function call
        # that returned an agent, if not, return the current agent
        agent = self.get_agent_from_last_function_call(history[-1].items)

        logger.info(
            "Selected agent at index %d (ID: %s, name: %s)",
            agent.id,
            agent.name,
        )
        self.current_agent = agent
        return agent

    def get_agent_from_last_function_call(self, content: list["ITEM_TYPES"]) -> "Agent":
        """Get the agent from the last function call in the history."""
        for item in content:
            if isinstance(item, FunctionResultContent) and isinstance(item.result, Agent):
                return item.result
        if self.current_agent is None:
            raise AgentChatException("No agent found in the last function call and no current agent set.")
        return self.current_agent
