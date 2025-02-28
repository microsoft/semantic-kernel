# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import AsyncIterable
from copy import deepcopy
from typing import TYPE_CHECKING, Any, cast

from pydantic import Field

from semantic_kernel.agents import Agent, AgentChat
from semantic_kernel.agents.strategies import (
    DefaultTerminationStrategy,
    SequentialSelectionStrategy,
)
from semantic_kernel.agents.strategies.selection.selection_strategy import SelectionStrategy
from semantic_kernel.agents.strategies.termination.termination_strategy import TerminationStrategy
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.history_reducer.chat_history_reducer import ChatHistoryReducer
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentChatException
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from semantic_kernel.contents.chat_history import ChatHistory

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class AgentGroupChat(AgentChat):
    """An agent chat that supports multi-turn interactions."""

    agent_ids: set[str]
    agents: list[Agent] = Field(default_factory=list)

    is_complete: bool = False
    termination_strategy: TerminationStrategy = Field(
        default_factory=DefaultTerminationStrategy,
        description="The termination strategy to use. The default strategy never terminates and has a max iterations of 5.",  # noqa: E501
    )
    selection_strategy: SelectionStrategy = Field(default_factory=SequentialSelectionStrategy)

    def __init__(
        self,
        agents: list[Agent] | None = None,
        termination_strategy: TerminationStrategy | None = None,
        selection_strategy: SelectionStrategy | None = None,
        chat_history: "ChatHistory | None" = None,
    ) -> None:
        """Initialize a new instance of AgentGroupChat.

        Args:
            agents: The agents to add to the group chat.
            termination_strategy: The termination strategy to use.
            selection_strategy: The selection strategy
            chat_history: The chat history.
        """
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
        if chat_history is not None:
            args["history"] = chat_history

        super().__init__(**args)

    def add_agent(self, agent: Agent) -> None:
        """Add an agent to the group chat.

        Args:
            agent: The agent to add.
        """
        if agent.id not in self.agent_ids:
            self.agent_ids.add(agent.id)
            self.agents.append(agent)

    async def invoke_single_turn(self, agent: Agent) -> AsyncIterable[ChatMessageContent]:
        """Invoke the agent chat for a single turn.

        Args:
            agent: The agent to invoke.

        Yields:
            The chat message.
        """
        async for message in self.invoke(agent, is_joining=True):
            if message.role == AuthorRole.ASSISTANT:
                task = self.termination_strategy.should_terminate(agent, self.history.messages)
                self.is_complete = await task
            yield message

    async def invoke_stream_single_turn(self, agent: Agent) -> AsyncIterable[ChatMessageContent]:
        """Invoke the agent chat for a single turn.

        Args:
            agent: The agent to invoke.

        Yields:
            The chat message.
        """
        async for message in self.invoke_stream(agent, is_joining=True):
            yield message

        self.is_complete = await self.termination_strategy.should_terminate(agent, self.history.messages)

    async def invoke(self, agent: Agent | None = None, is_joining: bool = True) -> AsyncIterable[ChatMessageContent]:
        """Invoke the agent chat asynchronously.

        Handles both group interactions and single agent interactions based on the provided arguments.

        Args:
            agent: The agent to invoke. If not provided, the method processes all agents in the chat.
            is_joining: Controls whether the agent joins the chat. Defaults to True.

        Yields:
            The chat message.
        """
        if agent is not None:
            if is_joining:
                self.add_agent(agent)

            async for message in super().invoke_agent(agent):
                if message.role == AuthorRole.ASSISTANT:
                    task = self.termination_strategy.should_terminate(agent, self.history.messages)
                    self.is_complete = await task
                yield message

            return

        if not self.agents:
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

    async def invoke_stream(
        self, agent: Agent | None = None, is_joining: bool = True
    ) -> AsyncIterable[ChatMessageContent]:
        """Invoke the agent chat stream asynchronously.

        Handles both group interactions and single agent interactions based on the provided arguments.

        Args:
            agent: The agent to invoke. If not provided, the method processes all agents in the chat.
            is_joining: Controls whether the agent joins the chat. Defaults to True.

        Yields:
            The chat message.
        """
        if agent is not None:
            if is_joining:
                self.add_agent(agent)

            async for message in super().invoke_agent_stream(agent):
                if message.role == AuthorRole.ASSISTANT:
                    task = self.termination_strategy.should_terminate(agent, self.history.messages)
                    self.is_complete = await task
                yield message

            return

        if not self.agents:
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

            async for message in super().invoke_agent_stream(selected_agent):
                yield message

            self.is_complete = await self.termination_strategy.should_terminate(selected_agent, self.history.messages)

            if self.is_complete:
                break

    async def reduce_history(self) -> bool:
        """Perform the reduction on the provided history, returning True if reduction occurred."""
        if not isinstance(self.history, ChatHistoryReducer):
            return False

        result = await self.history.reduce()
        if result is None:
            return False

        reducer = cast(ChatHistoryReducer, result)
        reduced_history = deepcopy(reducer.messages)
        await self.reset()
        await self.add_chat_messages(reduced_history)
        return True
