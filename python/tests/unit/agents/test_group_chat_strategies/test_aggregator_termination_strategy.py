# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock

from semantic_kernel.agents.strategies.termination.aggregator_termination_strategy import (
    AggregateTerminationCondition,
    AggregatorTerminationStrategy,
)
from semantic_kernel.agents.strategies.termination.termination_strategy import TerminationStrategy
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from tests.unit.agents.test_agent import MockAgent


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


def test_aggregator_is_termination_strategy():
    strategy1 = AsyncMock(spec=TerminationStrategy)
    strategy = AggregatorTerminationStrategy(strategies=[strategy1])
    assert isinstance(strategy, TerminationStrategy)
    assert issubclass(AggregatorTerminationStrategy, TerminationStrategy)


async def test_aggregator_should_agent_terminate():
    agent = MockAgent(id="test-agent-id")
    history = [MagicMock(spec=ChatMessageContent)]

    strategy1 = AsyncMock(spec=TerminationStrategy)
    strategy1.should_terminate.return_value = True

    strategy = AggregatorTerminationStrategy(strategies=[strategy1], condition=AggregateTerminationCondition.ALL)

    result = await strategy.should_agent_terminate(agent, history)

    assert result is True
    strategy1.should_terminate.assert_awaited_once_with(agent, history)


async def test_aggregator_should_terminate_agent_filtering():
    agent1 = MockAgent(id="agent-1")
    agent2 = MockAgent(id="agent-2")
    history = [MagicMock(spec=ChatMessageContent)]

    sub_strategy = AsyncMock(spec=TerminationStrategy)
    sub_strategy.should_terminate.return_value = True

    # Aggregator scoped only to agent1
    strategy = AggregatorTerminationStrategy(strategies=[sub_strategy], agents=[agent1])

    # Calling should_terminate for agent2 should be False and not invoke sub_strategy
    result = await strategy.should_terminate(agent2, history)
    assert result is False
    sub_strategy.should_terminate.assert_not_awaited()

    # Calling should_terminate for agent1 should evaluate sub_strategy
    result = await strategy.should_terminate(agent1, history)
    assert result is True
    sub_strategy.should_terminate.assert_awaited_once_with(agent1, history)


def test_aggregator_termination_strategy_with_agent_group_chat():
    from semantic_kernel.agents.group_chat.agent_group_chat import AgentGroupChat

    sub_strategy = AsyncMock(spec=TerminationStrategy)
    aggregator = AggregatorTerminationStrategy(
        strategies=[sub_strategy],
        maximum_iterations=10,
    )

    chat = AgentGroupChat(termination_strategy=aggregator)
    assert chat.termination_strategy == aggregator
    assert chat.termination_strategy.maximum_iterations == 10
