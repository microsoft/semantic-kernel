# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import AsyncIterable
from typing import Any

from pydantic import Field

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.agent_chat import AgentChat
from semantic_kernel.agents.strategies.selection.selection_strategy import (
    SelectionStrategy,
    SequentialSelectionStrategy,
)
from semantic_kernel.agents.strategies.termination.termination_strategy import TerminationStrategy
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentChatException

logger: logging.Logger = logging.getLogger(__name__)


class DefaultTerminationStrategy(TerminationStrategy):
    """A default termination strategy that never terminates."""

    maximum_iterations: int = 1

    async def should_agent_terminate(self, agent: Agent, history: list[ChatMessageContent]) -> bool:
        """Check if the agent should terminate."""
        return False


class AgentGroupChat(AgentChat):
    """An agent chat that supports multi-turn interactions."""

    agent_ids: set[str] = Field(default_factory=set)
    agents: list[Agent] = Field(default_factory=list)

    is_complete: bool = False
    termination_strategy: TerminationStrategy = Field(default_factory=DefaultTerminationStrategy)
    selection_strategy: SelectionStrategy = Field(default_factory=SequentialSelectionStrategy)

    def __init__(
        self,
        agents: list[Agent] | None = None,
        termination_strategy: TerminationStrategy | None = None,
        selection_strategy: SelectionStrategy | None = None,
    ) -> None:
        """Initialize a new instance of AgentGroupChat."""
        agent_ids = {agent.id for agent in agents} if agents else set()

        if agents is None:
            agents = []

        args: dict[str, Any] = {
            "agents": agents,
            "agent_ids": agent_ids,
        }

        if termination_strategy is not None:
            args["termination_strategy"] = termination_strategy
        if selection_strategy is not None:
            args["selection_strategy"] = selection_strategy

        super().__init__(**args)

    def add_agent(self, agent: Agent) -> None:
        """Add an agent to the group chat."""
        if agent.id not in self.agent_ids:
            self.agent_ids.add(agent.id)
            self.agents.append(agent)

    async def invoke_single_turn(self, agent: Agent) -> AsyncIterable[ChatMessageContent]:
        """Invoke the agent chat for a single turn."""
        async for message in self.invoke(agent, is_joining=True):
            if message.role == AuthorRole.ASSISTANT:
                task = self.termination_strategy.should_terminate(agent, self.history.messages)
                self.is_complete = await task
            yield message

    async def invoke(
        self, agent: Agent | None = None, is_joining: bool | None = False
    ) -> AsyncIterable[ChatMessageContent]:
        """Invoke the agent chat asynchronously."""
        # If agent and is_joining are provided, handle as single interaction.
        if agent is not None:
            # logging
            if is_joining:
                self.add_agent(agent)

            async for message in super().invoke_agent(agent):
                if message.role == AuthorRole.ASSISTANT:
                    task = self.termination_strategy.should_terminate(agent, self.history.messages)
                    self.is_complete = await task
                yield message

            # logger
            return

        # Default behavior if no agent is provided or is_joining is False.
        if self.agents is None:
            raise AgentChatException("No agents are available")

        if self.is_complete:
            if not self.termination_strategy.automatic_reset:
                raise AgentChatException("Chat is already complete")

            self.is_complete = False

        for _ in range(self.termination_strategy.maximum_iterations):
            try:
                selected_agent = await self.selection_strategy.next(self.agents, self.history.messages)
            except Exception as ex:
                logger.error(f"Failed to select agent: {ex}")
                raise AgentChatException("Failed to select agent") from ex

            async for message in super().invoke_agent(selected_agent):
                if message.role == AuthorRole.ASSISTANT:
                    task = self.termination_strategy.should_terminate(selected_agent, self.history.messages)
                    self.is_complete = await task
                yield message

            if self.is_complete:
                break
