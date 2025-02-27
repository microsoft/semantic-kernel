# Copyright (c) Microsoft. All rights reserved.

from unittest import mock
from unittest.mock import AsyncMock, MagicMock

import pytest

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.group_chat.agent_chat import AgentChat
from semantic_kernel.agents.group_chat.agent_group_chat import AgentGroupChat
from semantic_kernel.agents.strategies.selection.selection_strategy import SelectionStrategy
from semantic_kernel.agents.strategies.selection.sequential_selection_strategy import SequentialSelectionStrategy
from semantic_kernel.agents.strategies.termination.default_termination_strategy import DefaultTerminationStrategy
from semantic_kernel.agents.strategies.termination.termination_strategy import TerminationStrategy
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentChatException


@pytest.fixture
def agents():
    """Fixture that provides a list of mock agents."""
    return [MagicMock(spec=Agent, id=f"agent-{i}") for i in range(3)]


@pytest.fixture
def termination_strategy():
    """Fixture that provides a mock termination strategy."""
    return AsyncMock(spec=TerminationStrategy)


@pytest.fixture
def selection_strategy():
    """Fixture that provides a mock selection strategy."""
    return AsyncMock(spec=SelectionStrategy)


# region Non-Streaming


def test_agent_group_chat_initialization(agents, termination_strategy, selection_strategy):
    group_chat = AgentGroupChat(
        agents=agents, termination_strategy=termination_strategy, selection_strategy=selection_strategy
    )

    assert group_chat.agents == agents
    assert group_chat.agent_ids == {agent.id for agent in agents}
    assert group_chat.termination_strategy == termination_strategy
    assert group_chat.selection_strategy == selection_strategy


def test_agent_group_chat_initialization_defaults():
    group_chat = AgentGroupChat()

    assert group_chat.agents == []
    assert group_chat.agent_ids == set()
    assert isinstance(group_chat.termination_strategy, DefaultTerminationStrategy)
    assert isinstance(group_chat.selection_strategy, SequentialSelectionStrategy)


def test_add_agent(agents):
    group_chat = AgentGroupChat()

    group_chat.add_agent(agents[0])

    assert agents[0] in group_chat.agents
    assert agents[0].id in group_chat.agent_ids


def test_add_duplicate_agent(agents):
    group_chat = AgentGroupChat(agents=[agents[0]])

    group_chat.add_agent(agents[0])

    assert len(group_chat.agents) == 1
    assert len(group_chat.agent_ids) == 1


async def test_invoke_single_turn(agents, termination_strategy):
    group_chat = AgentGroupChat(termination_strategy=termination_strategy)

    async def mock_invoke(agent, is_joining=True):
        yield MagicMock(role=AuthorRole.ASSISTANT)

    with mock.patch.object(AgentGroupChat, "invoke", side_effect=mock_invoke):
        termination_strategy.should_terminate.return_value = False

        async for message in group_chat.invoke_single_turn(agents[0]):
            assert message.role == AuthorRole.ASSISTANT

        termination_strategy.should_terminate.assert_awaited_once()


async def test_invoke_single_turn_sets_complete(agents, termination_strategy):
    group_chat = AgentGroupChat(termination_strategy=termination_strategy)

    async def mock_invoke(agent, is_joining=True):
        yield MagicMock(role=AuthorRole.ASSISTANT)

    with mock.patch.object(AgentGroupChat, "invoke", side_effect=mock_invoke):
        termination_strategy.should_terminate.return_value = True

        async for _ in group_chat.invoke_single_turn(agents[0]):
            pass

        assert group_chat.is_complete is True
        termination_strategy.should_terminate.assert_awaited_once()


async def test_invoke_with_agent_joining(agents, termination_strategy):
    for agent in agents:
        agent.name = f"Agent {agent.id}"
        agent.id = f"agent-{agent.id}"

    group_chat = AgentGroupChat(termination_strategy=termination_strategy)

    with (
        mock.patch.object(AgentGroupChat, "add_agent", autospec=True) as mock_add_agent,
        mock.patch.object(AgentChat, "invoke_agent", autospec=True) as mock_invoke_agent,
    ):

        async def mock_invoke_gen(*args, **kwargs):
            yield MagicMock(role=AuthorRole.ASSISTANT)

        mock_invoke_agent.side_effect = mock_invoke_gen

        async for _ in group_chat.invoke(agents[0], is_joining=True):
            pass

        mock_add_agent.assert_called_once_with(group_chat, agents[0])


async def test_invoke_with_complete_chat(agents, termination_strategy):
    termination_strategy.automatic_reset = False
    group_chat = AgentGroupChat(agents=agents, termination_strategy=termination_strategy)
    group_chat.is_complete = True

    with pytest.raises(AgentChatException, match="Chat is already complete"):
        async for _ in group_chat.invoke():
            pass


async def test_invoke_agent_with_none_defined_errors(agents):
    group_chat = AgentGroupChat()

    with pytest.raises(AgentChatException, match="No agents are available"):
        async for _ in group_chat.invoke():
            pass


async def test_invoke_selection_strategy_error(agents, selection_strategy):
    group_chat = AgentGroupChat(agents=agents, selection_strategy=selection_strategy)

    selection_strategy.next.side_effect = Exception("Selection failed")

    with pytest.raises(AgentChatException, match="Failed to select agent"):
        async for _ in group_chat.invoke():
            pass


async def test_invoke_iterations(agents, termination_strategy, selection_strategy):
    for agent in agents:
        agent.name = f"Agent {agent.id}"
        agent.id = f"agent-{agent.id}"

    termination_strategy.maximum_iterations = 2

    group_chat = AgentGroupChat(
        agents=agents, termination_strategy=termination_strategy, selection_strategy=selection_strategy
    )

    selection_strategy.next.side_effect = lambda agents, history: agents[0]

    async def mock_invoke_agent(*args, **kwargs):
        yield MagicMock(role=AuthorRole.ASSISTANT)

    with mock.patch.object(AgentChat, "invoke_agent", side_effect=mock_invoke_agent):
        termination_strategy.should_terminate.return_value = False

        iteration_count = 0
        async for _ in group_chat.invoke():
            iteration_count += 1

        assert iteration_count == 2


async def test_invoke_is_complete_then_reset(agents, termination_strategy, selection_strategy):
    for agent in agents:
        agent.name = f"Agent {agent.id}"
        agent.id = f"agent-{agent.id}"

    termination_strategy.maximum_iterations = 2
    termination_strategy.automatic_reset = True

    group_chat = AgentGroupChat(
        agents=agents, termination_strategy=termination_strategy, selection_strategy=selection_strategy
    )

    group_chat.is_complete = True

    selection_strategy.next.side_effect = lambda agents, history: agents[0]

    async def mock_invoke_agent(*args, **kwargs):
        yield MagicMock(role=AuthorRole.ASSISTANT)

    with mock.patch.object(AgentChat, "invoke_agent", side_effect=mock_invoke_agent):
        termination_strategy.should_terminate.return_value = False

        iteration_count = 0
        async for _ in group_chat.invoke():
            iteration_count += 1

        assert iteration_count == 2


# endregion

# region Streaming


async def test_invoke_streaming_single_turn(agents, termination_strategy):
    group_chat = AgentGroupChat(termination_strategy=termination_strategy)

    async def mock_invoke(agent, is_joining=True):
        yield MagicMock(role=AuthorRole.ASSISTANT)

    with mock.patch.object(AgentGroupChat, "invoke_stream", side_effect=mock_invoke):
        termination_strategy.should_terminate.return_value = False

        async for message in group_chat.invoke_stream_single_turn(agents[0]):
            assert message.role == AuthorRole.ASSISTANT

        termination_strategy.should_terminate.assert_awaited_once()


async def test_invoke_stream_with_agent_joining(agents, termination_strategy):
    for agent in agents:
        agent.name = f"Agent {agent.id}"
        agent.id = f"agent-{agent.id}"

    group_chat = AgentGroupChat(termination_strategy=termination_strategy)

    with (
        mock.patch.object(AgentGroupChat, "add_agent", autospec=True) as mock_add_agent,
        mock.patch.object(AgentChat, "invoke_agent_stream", autospec=True) as mock_invoke_agent,
    ):

        async def mock_invoke_gen(*args, **kwargs):
            yield MagicMock(role=AuthorRole.ASSISTANT)

        mock_invoke_agent.side_effect = mock_invoke_gen

        async for _ in group_chat.invoke_stream(agents[0], is_joining=True):
            pass

        mock_add_agent.assert_called_once_with(group_chat, agents[0])


async def test_invoke_stream_with_complete_chat(agents, termination_strategy):
    termination_strategy.automatic_reset = False
    group_chat = AgentGroupChat(agents=agents, termination_strategy=termination_strategy)
    group_chat.is_complete = True

    with pytest.raises(AgentChatException, match="Chat is already complete"):
        async for _ in group_chat.invoke_stream():
            pass


async def test_invoke_stream_selection_strategy_error(agents, selection_strategy):
    group_chat = AgentGroupChat(agents=agents, selection_strategy=selection_strategy)

    selection_strategy.next.side_effect = Exception("Selection failed")

    with pytest.raises(AgentChatException, match="Failed to select agent"):
        async for _ in group_chat.invoke_stream():
            pass


async def test_invoke_stream_iterations(agents, termination_strategy, selection_strategy):
    for agent in agents:
        agent.name = f"Agent {agent.id}"
        agent.id = f"agent-{agent.id}"

    termination_strategy.maximum_iterations = 2

    group_chat = AgentGroupChat(
        agents=agents, termination_strategy=termination_strategy, selection_strategy=selection_strategy
    )

    selection_strategy.next.side_effect = lambda agents, history: agents[0]

    async def mock_invoke_agent(*args, **kwargs):
        yield MagicMock(role=AuthorRole.ASSISTANT)

    with mock.patch.object(AgentChat, "invoke_agent_stream", side_effect=mock_invoke_agent):
        termination_strategy.should_terminate.return_value = False

        iteration_count = 0
        async for _ in group_chat.invoke_stream():
            iteration_count += 1

        assert iteration_count == 2


async def test_invoke_stream_is_complete_then_reset(agents, termination_strategy, selection_strategy):
    for agent in agents:
        agent.name = f"Agent {agent.id}"
        agent.id = f"agent-{agent.id}"

    termination_strategy.maximum_iterations = 2
    termination_strategy.automatic_reset = True

    group_chat = AgentGroupChat(
        agents=agents, termination_strategy=termination_strategy, selection_strategy=selection_strategy
    )

    group_chat.is_complete = True

    selection_strategy.next.side_effect = lambda agents, history: agents[0]

    async def mock_invoke_agent(*args, **kwargs):
        yield MagicMock(role=AuthorRole.ASSISTANT)

    with mock.patch.object(AgentChat, "invoke_agent_stream", side_effect=mock_invoke_agent):
        termination_strategy.should_terminate.return_value = False

        iteration_count = 0
        async for _ in group_chat.invoke_stream():
            iteration_count += 1

        assert iteration_count == 2


async def test_invoke_streaming_agent_with_none_defined_errors(agents):
    group_chat = AgentGroupChat()

    with pytest.raises(AgentChatException, match="No agents are available"):
        async for _ in group_chat.invoke_stream():
            pass


# endregion
