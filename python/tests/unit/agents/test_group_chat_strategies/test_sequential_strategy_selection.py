# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import MagicMock

import pytest

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.strategies.selection.sequential_selection_strategy import SequentialSelectionStrategy
from semantic_kernel.exceptions.agent_exceptions import AgentExecutionException
from tests.unit.agents.test_agent import MockAgent


@pytest.fixture
def agents():
    """Fixture that provides a list of mock agents."""
    return [MockAgent(id=f"agent-{i}") for i in range(3)]


async def test_sequential_selection_next(agents):
    strategy = SequentialSelectionStrategy()

    # Test the sequence of selections
    selected_agent_1 = await strategy.next(agents, [])
    selected_agent_2 = await strategy.next(agents, [])
    selected_agent_3 = await strategy.next(agents, [])

    assert selected_agent_1.id == "agent-0"
    assert selected_agent_2.id == "agent-1"
    assert selected_agent_3.id == "agent-2"


async def test_sequential_selection_wraps_around(agents):
    strategy = SequentialSelectionStrategy()

    for _ in range(3):
        await strategy.next(agents, [])

    selected_agent = await strategy.next(agents, [])
    assert selected_agent.id == "agent-0"


async def test_sequential_selection_reset(agents):
    strategy = SequentialSelectionStrategy()

    # Move the index to the middle of the list
    await strategy.next(agents, [])
    await strategy.next(agents, [])

    strategy.reset()

    selected_agent = await strategy.next(agents, [])
    assert selected_agent.id == "agent-0"


async def test_sequential_selection_exceeds_length(agents):
    strategy = SequentialSelectionStrategy()

    strategy._index = len(agents)

    selected_agent = await strategy.next(agents, [])

    assert selected_agent.id == "agent-0"
    assert strategy._index == 0

    selected_agent = await strategy.next(agents, [])

    assert selected_agent.id == "agent-1"
    assert strategy._index == 1


async def test_sequential_selection_empty_agents():
    strategy = SequentialSelectionStrategy()

    with pytest.raises(AgentExecutionException) as excinfo:
        await strategy.next([], [])

    assert "Agent Failure - No agents present to select." in str(excinfo.value)


async def test_sequential_selection_avoid_selecting_same_agent_twice():
    # Arrange
    agent_0 = MagicMock(spec=Agent)
    agent_0.id = "agent-0"
    agent_0.name = "Agent0"
    agent_0.plugins = []

    agent_1 = MagicMock(spec=Agent)
    agent_1.id = "agent-1"
    agent_1.name = "Agent1"
    agent_1.plugins = []

    agents = [agent_0, agent_1]

    strategy = SequentialSelectionStrategy()
    # Simulate that we've already selected an agent once:
    strategy.has_selected = True
    # Set the initial agent to the first agent
    strategy.initial_agent = agent_0
    # Ensure the internal index is set to -1
    strategy._index = -1

    # Act
    selected_agent = await strategy.next(agents, [])

    # Assert
    # According to the condition, we should skip selecting agent_0 again
    assert selected_agent.id == "agent-1"
    assert strategy._index == 1
