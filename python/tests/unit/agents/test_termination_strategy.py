# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock

import pytest

from semantic_kernel.agents import Agent
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.agents.strategies.termination.termination_strategy import TerminationStrategy
from semantic_kernel.contents.chat_message_content import ChatMessageContent


class MockAgent(Agent):
    """A mock agent for testing purposes."""

    def __init__(self, id: str = None, name: str = "Test Agent", description: str = "A test agent"):
        args = {
            "name": name,
            "description": description,
        }
        if id is not None:
            args["id"] = id
        super().__init__(**args)

    def get_channel_keys(self) -> list[str]:
        return ["key1", "key2"]

    async def create_channel(self) -> AgentChannel:
        return AsyncMock(spec=AgentChannel)


class TestTerminationStrategy(TerminationStrategy):
    """A test implementation of TerminationStrategy for testing purposes."""

    async def should_agent_terminate(self, agent: "Agent", history: list[ChatMessageContent]) -> bool:
        """Simple test implementation that always returns True."""
        return True


@pytest.mark.asyncio
async def test_should_terminate_with_matching_agent():
    agent = MockAgent(id="test-agent-id")
    strategy = TestTerminationStrategy(agents=[agent])

    # Assuming history is a list of ChatMessageContent; can be mocked or made minimal
    history = [MagicMock(spec=ChatMessageContent)]

    result = await strategy.should_terminate(agent, history)
    assert result is True


@pytest.mark.asyncio
async def test_should_terminate_with_non_matching_agent():
    agent = MockAgent(id="test-agent-id")
    non_matching_agent = MockAgent(id="non-matching-agent-id")
    strategy = TestTerminationStrategy(agents=[non_matching_agent])

    # Assuming history is a list of ChatMessageContent; can be mocked or made minimal
    history = [MagicMock(spec=ChatMessageContent)]

    result = await strategy.should_terminate(agent, history)
    assert result is False


@pytest.mark.asyncio
async def test_should_terminate_no_agents_in_strategy():
    agent = MockAgent(id="test-agent-id")
    strategy = TestTerminationStrategy()

    # Assuming history is a list of ChatMessageContent; can be mocked or made minimal
    history = [MagicMock(spec=ChatMessageContent)]

    result = await strategy.should_terminate(agent, history)
    assert result is True


@pytest.mark.asyncio
async def test_should_agent_terminate_not_implemented():
    agent = MockAgent(id="test-agent-id")
    strategy = TerminationStrategy(agents=[agent])

    # Assuming history is a list of ChatMessageContent; can be mocked or made minimal
    history = [MagicMock(spec=ChatMessageContent)]

    with pytest.raises(NotImplementedError):
        await strategy.should_agent_terminate(agent, history)
