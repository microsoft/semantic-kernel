# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING

from pydantic import PrivateAttr

from semantic_kernel.agents.strategies.selection.selection_strategy import SelectionStrategy
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.agents import Agent
    from semantic_kernel.contents.chat_message_content import ChatMessageContent


@experimental_class
class SequentialSelectionStrategy(SelectionStrategy):
    """A selection strategy that selects agents in a sequential order."""

    _index: int = PrivateAttr(default=0)

    def reset(self):
        """Reset the index."""
        self._index = 0

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

        if self._index >= len(agents):
            self.reset()

        agent = agents[self._index]

        self._index = (self._index + 1) % len(agents)

        return agent
