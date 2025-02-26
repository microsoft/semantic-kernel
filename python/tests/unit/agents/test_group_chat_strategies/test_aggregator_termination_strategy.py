# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.agents.strategies.termination.aggregator_termination_strategy import (
    AggregateTerminationCondition,
    AggregatorTerminationStrategy,
)
from semantic_kernel.agents.strategies.termination.termination_strategy import TerminationStrategy
from semantic_kernel.contents.chat_message_content import ChatMessageContent


class MockAgent(Agent):
    """A mock agent for testing purposes."""

    def __init__(self, id: str = None, name: str = "TestAgent", description: str = "A test agent"):
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


async def test_aggregate_termination_condition_all_true():
    agent = MockAgent(id="test-agent-id")
    history = [MagicMock(spec=ChatMessageContent)]

    # Mocking two strategies that return True
    strategy1 = AsyncMock(spec=TerminationStrategy)
    strategy1.should_terminate.return_value = True

    strategy2 = AsyncMock(spec=TerminationStrategy)
    strategy2.should_terminate.return_value = True

    strategy = AggregatorTerminationStrategy(
        strategies=[strategy1, strategy2], condition=AggregateTerminationCondition.ALL
    )

    result = await strategy.should_terminate_async(agent, history)

    assert result is True
    strategy1.should_terminate.assert_awaited_once()
    strategy2.should_terminate.assert_awaited_once()


async def test_aggregate_termination_condition_all_false():
    agent = MockAgent(id="test-agent-id")
    history = [MagicMock(spec=ChatMessageContent)]

    # Mocking two strategies, one returns True, the other False
    strategy1 = AsyncMock(spec=TerminationStrategy)
    strategy1.should_terminate.return_value = True

    strategy2 = AsyncMock(spec=TerminationStrategy)
    strategy2.should_terminate.return_value = False

    strategy = AggregatorTerminationStrategy(
        strategies=[strategy1, strategy2], condition=AggregateTerminationCondition.ALL
    )

    result = await strategy.should_terminate_async(agent, history)

    assert result is False
    strategy1.should_terminate.assert_awaited_once()
    strategy2.should_terminate.assert_awaited_once()


async def test_aggregate_termination_condition_any_true():
    agent = MockAgent(id="test-agent-id")
    history = [MagicMock(spec=ChatMessageContent)]

    # Mocking two strategies, one returns False, the other True
    strategy1 = AsyncMock(spec=TerminationStrategy)
    strategy1.should_terminate.return_value = False

    strategy2 = AsyncMock(spec=TerminationStrategy)
    strategy2.should_terminate.return_value = True

    strategy = AggregatorTerminationStrategy(
        strategies=[strategy1, strategy2], condition=AggregateTerminationCondition.ANY
    )

    result = await strategy.should_terminate_async(agent, history)

    assert result is True
    strategy1.should_terminate.assert_awaited_once()
    strategy2.should_terminate.assert_awaited_once()


async def test_aggregate_termination_condition_any_false():
    agent = MockAgent(id="test-agent-id")
    history = [MagicMock(spec=ChatMessageContent)]

    # Mocking two strategies that return False
    strategy1 = AsyncMock(spec=TerminationStrategy)
    strategy1.should_terminate.return_value = False

    strategy2 = AsyncMock(spec=TerminationStrategy)
    strategy2.should_terminate.return_value = False

    strategy = AggregatorTerminationStrategy(
        strategies=[strategy1, strategy2], condition=AggregateTerminationCondition.ANY
    )

    result = await strategy.should_terminate_async(agent, history)

    assert result is False
    strategy1.should_terminate.assert_awaited_once()
    strategy2.should_terminate.assert_awaited_once()
