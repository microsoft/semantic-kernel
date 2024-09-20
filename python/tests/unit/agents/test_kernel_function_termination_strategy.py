# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.agents.strategies import KernelFunctionTerminationStrategy
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.kernel import Kernel


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


@pytest.mark.asyncio
async def test_should_agent_terminate_with_result_true():
    agent = MockAgent(id="test-agent-id")
    history = [MagicMock(spec=ChatMessageContent)]

    mock_function = AsyncMock(spec=KernelFunction)
    mock_function.invoke.return_value = MagicMock(value=True)
    mock_kernel = MagicMock(spec=Kernel)

    strategy = KernelFunctionTerminationStrategy(
        agents=[agent], function=mock_function, kernel=mock_kernel, result_parser=lambda result: result.value
    )

    result = await strategy.should_agent_terminate(agent, history)

    assert result is True
    mock_function.invoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_should_agent_terminate_with_result_false():
    agent = MockAgent(id="test-agent-id")
    history = [MagicMock(spec=ChatMessageContent)]

    mock_function = AsyncMock(spec=KernelFunction)
    mock_function.invoke.return_value = MagicMock(value=False)
    mock_kernel = MagicMock(spec=Kernel)

    strategy = KernelFunctionTerminationStrategy(
        agents=[agent], function=mock_function, kernel=mock_kernel, result_parser=lambda result: result.value
    )

    result = await strategy.should_agent_terminate(agent, history)

    assert result is False
    mock_function.invoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_should_agent_terminate_with_none_result():
    agent = MockAgent(id="test-agent-id")
    history = [MagicMock(spec=ChatMessageContent)]

    mock_function = AsyncMock(spec=KernelFunction)
    mock_function.invoke.return_value = None
    mock_kernel = MagicMock(spec=Kernel)

    strategy = KernelFunctionTerminationStrategy(
        agents=[agent],
        function=mock_function,
        kernel=mock_kernel,
        result_parser=lambda result: result.value if result else False,
    )

    result = await strategy.should_agent_terminate(agent, history)

    assert result is False
    mock_function.invoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_should_agent_terminate_custom_arguments():
    agent = MockAgent(id="test-agent-id")
    history = [MagicMock(spec=ChatMessageContent)]

    mock_function = AsyncMock(spec=KernelFunction)
    mock_function.invoke.return_value = MagicMock(value=True)
    mock_kernel = MagicMock(spec=Kernel)

    custom_args = KernelArguments(execution_settings={"some_setting": MagicMock(model_dump=lambda: {"key": "value"})})

    strategy = KernelFunctionTerminationStrategy(
        agents=[agent],
        function=mock_function,
        kernel=mock_kernel,
        arguments=custom_args,
        result_parser=lambda result: result.value,
    )

    with patch.object(KernelArguments, "__init__", return_value=None) as mock_init:
        result = await strategy.should_agent_terminate(agent, history)
        mock_init.assert_called_once()

    assert result is True
    mock_function.invoke.assert_awaited_once()


@pytest.mark.asyncio
async def test_should_agent_terminate_result_parser_awaitable():
    agent = MockAgent(id="test-agent-id")
    history = [MagicMock(spec=ChatMessageContent)]

    mock_function = AsyncMock(spec=KernelFunction)
    mock_function.invoke.return_value = MagicMock(value=True)
    mock_kernel = MagicMock(spec=Kernel)

    async def mock_result_parser(result):
        return result.value

    strategy = KernelFunctionTerminationStrategy(
        agents=[agent], function=mock_function, kernel=mock_kernel, result_parser=mock_result_parser
    )

    result = await strategy.should_agent_terminate(agent, history)

    assert result is True
    mock_function.invoke.assert_awaited_once()
