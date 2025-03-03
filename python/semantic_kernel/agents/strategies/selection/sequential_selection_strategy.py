# Copyright (c) Microsoft. All rights reserved.

import logging
import sys

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from typing import TYPE_CHECKING

from pydantic import PrivateAttr

from semantic_kernel.agents.strategies.selection.selection_strategy import SelectionStrategy
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from semantic_kernel.agents import Agent
    from semantic_kernel.contents.chat_message_content import ChatMessageContent


logger: logging.Logger = logging.getLogger(__name__)


@experimental
class SequentialSelectionStrategy(SelectionStrategy):
    """Round-robin turn-taking strategy. Agent order is based on the order in which they joined."""

    _index: int = PrivateAttr(default=-1)

    def reset(self) -> None:
        """Reset selection to the initial/first agent."""
        self._index = -1

    def _increment_index(self, agent_count: int) -> None:
        """Increment the index in a circular manner."""
        self._index = (self._index + 1) % agent_count

    @override
    async def select_agent(
        self,
        agents: list["Agent"],
        history: list["ChatMessageContent"],
    ) -> "Agent":
        """Select the next agent in a round-robin fashion.

        Args:
            agents: The list of agents to select from.
            history: The history of messages in the conversation.

        Returns:
            The agent who takes the next turn.
        """
        if self._index >= len(agents):
            self._index = -1

        if (
            self.has_selected
            and self.initial_agent is not None
            and len(agents) > 0
            and agents[0] == self.initial_agent
            and self._index < 0
        ):
            # Avoid selecting the same agent twice in a row
            self._increment_index(len(agents))

        # Main index increment
        self._increment_index(len(agents))

        # Pick the agent
        agent = agents[self._index]

        logger.info(
            "Selected agent at index %d (ID: %s, name: %s)",
            self._index,
            agent.id,
            agent.name,
        )
        return agent
