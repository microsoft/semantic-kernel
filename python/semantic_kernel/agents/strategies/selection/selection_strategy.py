# Copyright (c) Microsoft. All rights reserved.

from abc import ABC
from typing import TYPE_CHECKING

from semantic_kernel.agents import Agent
from semantic_kernel.exceptions.agent_exceptions import AgentExecutionException
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from semantic_kernel.contents.chat_message_content import ChatMessageContent


@experimental
class SelectionStrategy(KernelBaseModel, ABC):
    """Base strategy class for selecting the next agent in a chat."""

    has_selected: bool = False
    initial_agent: Agent | None = None

    async def next(
        self,
        agents: list[Agent],
        history: list["ChatMessageContent"],
    ) -> Agent:
        """Select the next agent to interact with.

        Args:
            agents: The list of agents to select from.
            history: The history of messages in the conversation.

        Returns:
            The agent who takes the next turn.
        """
        if not agents and self.initial_agent is None:
            raise AgentExecutionException("Agent Failure - No agents present to select.")

        # If it's the first selection and we have an initial agent, use it
        if not self.has_selected and self.initial_agent is not None:
            agent = self.initial_agent
        else:
            agent = await self.select_agent(agents, history)

        self.has_selected = True
        return agent

    async def select_agent(
        self,
        agents: list[Agent],
        history: list["ChatMessageContent"],
    ) -> Agent:
        """Determines which agent goes next. Override for custom logic.

        By default, this fallback returns the first agent in the list.
        """
        return agents[0]
