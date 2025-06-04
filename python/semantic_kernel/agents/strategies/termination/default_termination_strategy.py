# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING

from pydantic import Field

from semantic_kernel.agents.strategies.termination.termination_strategy import TerminationStrategy
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from semantic_kernel.agents.agent import Agent
    from semantic_kernel.contents.chat_message_content import ChatMessageContent


@experimental
class DefaultTerminationStrategy(TerminationStrategy):
    """A default termination strategy that never terminates."""

    maximum_iterations: int = Field(default=5, description="The maximum number of iterations to run the agent.")

    async def should_agent_terminate(self, agent: "Agent", history: list["ChatMessageContent"]) -> bool:
        """Check if the agent should terminate.

        Args:
            agent: The agent to check.
            history: The history of messages in the conversation.

        Returns:
            Defaults to False for the default strategy
        """
        return False
