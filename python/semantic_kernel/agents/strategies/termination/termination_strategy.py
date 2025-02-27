# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import TYPE_CHECKING

from pydantic import Field

from semantic_kernel.agents.agent import Agent
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from semantic_kernel.contents.chat_message_content import ChatMessageContent

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class TerminationStrategy(KernelBaseModel):
    """A strategy for determining when an agent should terminate."""

    maximum_iterations: int = Field(default=99)
    automatic_reset: bool = False
    agents: list[Agent] = Field(default_factory=list)

    async def should_agent_terminate(self, agent: "Agent", history: list["ChatMessageContent"]) -> bool:
        """Check if the agent should terminate.

        Args:
            agent: The agent to check.
            history: The history of messages in the conversation.

        Returns:
            True if the agent should terminate, False otherwise
        """
        raise NotImplementedError("Subclasses should implement this method")

    async def should_terminate(self, agent: "Agent", history: list["ChatMessageContent"]) -> bool:
        """Check if the agent should terminate.

        Args:
            agent: The agent to check.
            history: The history of messages in the conversation.

        Returns:
            True if the agent should terminate, False otherwise
        """
        logger.info(f"Evaluating termination criteria for {agent.id}")

        if self.agents and not any(a.id == agent.id for a in self.agents):
            logger.info(f"Agent {agent.id} is out of scope")
            return False

        should_terminate = await self.should_agent_terminate(agent, history)

        logger.info(f"Evaluated criteria for {agent.id}, should terminate: {should_terminate}")
        return should_terminate
