# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import TYPE_CHECKING

from pydantic import Field

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.kernel_pydantic import KernelBaseModel

if TYPE_CHECKING:
    from semantic_kernel.agents.agent import Agent

logger: logging.Logger = logging.getLogger(__name__)


class TerminationStrategy(KernelBaseModel):
    """A strategy for determining when an agent should terminate."""

    maximum_iterations: int = Field(default=99)
    automatic_reset: bool = False
    agents: list["Agent"] = Field(default_factory=list)

    async def should_agent_terminate(self, agent: "Agent", history: list[ChatMessageContent]) -> bool:
        """Check if the agent should terminate."""
        raise NotImplementedError("Subclasses should implement this method")

    async def should_terminate(self, agent: "Agent", history: list[ChatMessageContent]) -> bool:
        """Check if the agent should terminate."""
        logger.info(f"Evaluating termination criteria for {agent.id}")

        # `agents` must contain `agent`, if `agents` is not empty.
        if self.agents and not any(a.id == agent.id for a in self.agents):
            logger.info(f"Agent {agent.id} is out of scope")
            return False

        should_terminate = await self.should_agent_terminate(agent, history)

        logger.info(f"Evaluated criteria for {agent.id}, should terminate: {should_terminate}")
        return should_terminate
