# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock

import pytest

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.agents.strategies.selection.sequential_selection_strategy import SequentialSelectionStrategy


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


@pytest.fixture
def agents():
    """Fixture that provides a list of mock agents."""
    return [MockAgent(id=f"agent-{i}") for i in range(3)]


@pytest.mark.asyncio
async def test_sequential_selection_next(agents):
    strategy = SequentialSelectionStrategy()

    # Test the sequence of selections
    selected_agent_1 = await strategy.next(agents, [])
    selected_agent_2 = await strategy.next(agents, [])
    selected_agent_3 = await strategy.next(agents, [])

    assert selected_agent_1.id == "agent-0"
    assert selected_agent_2.id == "agent-1"
    assert selected_agent_3.id == "agent-2"


@pytest.mark.asyncio
async def test_sequential_selection_wraps_around(agents):
    strategy = SequentialSelectionStrategy()

    for _ in range(3):
        await strategy.next(agents, [])

    selected_agent = await strategy.next(agents, [])
    assert selected_agent.id == "agent-0"


@pytest.mark.asyncio
async def test_sequential_selection_reset(agents):
    strategy = SequentialSelectionStrategy()

    # Move the index to the middle of the list
    await strategy.next(agents, [])
    await strategy.next(agents, [])

    strategy.reset()

    selected_agent = await strategy.next(agents, [])
    assert selected_agent.id == "agent-0"


@pytest.mark.asyncio
async def test_sequential_selection_exceeds_length(agents):
    strategy = SequentialSelectionStrategy()

    strategy._index = len(agents)

    selected_agent = await strategy.next(agents, [])

    assert selected_agent.id == "agent-0"
    assert strategy._index == 1


@pytest.mark.asyncio
async def test_sequential_selection_empty_agents():
    strategy = SequentialSelectionStrategy()

    with pytest.raises(ValueError) as excinfo:
        await strategy.next([], [])

    assert "No agents to select from" in str(excinfo.value)
