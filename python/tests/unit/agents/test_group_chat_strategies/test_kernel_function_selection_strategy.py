# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock

import pytest

from semantic_kernel.agents.strategies.selection.kernel_function_selection_strategy import (
    KernelFunctionSelectionStrategy,
)
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.exceptions.agent_exceptions import AgentExecutionException
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.kernel import Kernel
from tests.unit.agents.test_agent import MockAgent


@pytest.fixture
def agents():
    """Fixture that provides a list of mock agents."""
    return [MockAgent(id=f"agent-{i}", name=f"Agent_{i}") for i in range(3)]


async def test_kernel_function_selection_next_success(agents):
    history = [MagicMock(spec=ChatMessageContent)]
    mock_function = AsyncMock(spec=KernelFunction)
    mock_function.invoke.return_value = MagicMock(value="Agent_1")
    mock_kernel = MagicMock(spec=Kernel)

    strategy = KernelFunctionSelectionStrategy(
        function=mock_function, kernel=mock_kernel, result_parser=lambda result: result.value
    )

    selected_agent = await strategy.next(agents, history)

    assert selected_agent.name == "Agent_1"
    mock_function.invoke.assert_awaited_once()


async def test_kernel_function_selection_next_agent_not_found(agents):
    history = [MagicMock(spec=ChatMessageContent)]
    mock_function = AsyncMock(spec=KernelFunction)
    mock_function.invoke.return_value = MagicMock(value="Nonexistent-Agent")
    mock_kernel = MagicMock(spec=Kernel)

    strategy = KernelFunctionSelectionStrategy(
        function=mock_function, kernel=mock_kernel, result_parser=lambda result: result.value
    )

    with pytest.raises(AgentExecutionException) as excinfo:
        await strategy.next(agents, history)

    assert "Strategy unable to select next agent" in str(excinfo.value)
    mock_function.invoke.assert_awaited_once()


async def test_kernel_function_selection_next_result_is_none(agents):
    history = [MagicMock(spec=ChatMessageContent)]
    mock_function = AsyncMock(spec=KernelFunction)
    mock_function.invoke.return_value = None
    mock_kernel = MagicMock(spec=Kernel)

    strategy = KernelFunctionSelectionStrategy(
        function=mock_function, kernel=mock_kernel, result_parser=lambda result: result.value if result else None
    )

    with pytest.raises(AgentExecutionException) as excinfo:
        await strategy.next(agents, history)

    assert "Strategy unable to determine next agent" in str(excinfo.value)
    mock_function.invoke.assert_awaited_once()


async def test_kernel_function_selection_next_exception_during_invoke(agents):
    history = [MagicMock(spec=ChatMessageContent)]
    mock_function = AsyncMock(spec=KernelFunction)
    mock_function.invoke.side_effect = Exception("Test exception")
    mock_kernel = MagicMock(spec=Kernel)

    strategy = KernelFunctionSelectionStrategy(
        function=mock_function, kernel=mock_kernel, result_parser=lambda result: result.value
    )

    with pytest.raises(AgentExecutionException) as excinfo:
        await strategy.next(agents, history)

    assert "Strategy failed to execute function" in str(excinfo.value)
    mock_function.invoke.assert_awaited_once()


async def test_kernel_function_selection_result_parser_is_async(agents):
    history = [MagicMock(spec=ChatMessageContent)]
    mock_function = AsyncMock(spec=KernelFunction)
    mock_function.invoke.return_value = MagicMock(value="Agent_2")
    mock_kernel = MagicMock(spec=Kernel)

    async def async_result_parser(result):
        return result.value

    strategy = KernelFunctionSelectionStrategy(
        function=mock_function, kernel=mock_kernel, result_parser=async_result_parser
    )

    selected_agent = await strategy.next(agents, history)

    assert selected_agent.name == "Agent_2"
    mock_function.invoke.assert_awaited_once()
