# Copyright (c) Microsoft. All rights reserved.

import asyncio
import sys
from unittest.mock import patch

import pytest

from semantic_kernel.agents.orchestration.concurrent import ConcurrentOrchestration
from semantic_kernel.agents.orchestration.orchestration_base import DefaultTypeAlias, OrchestrationResult
from semantic_kernel.agents.runtime.in_process.in_process_runtime import InProcessRuntime
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from tests.unit.agents.orchestration.conftest import MockAgent, MockRuntime


async def test_prepare():
    """Test the prepare method of the ConcurrentOrchestration."""
    agent_a = MockAgent()
    agent_b = MockAgent()

    runtime = MockRuntime()

    package_path = "semantic_kernel.agents.orchestration.concurrent"
    with (
        patch(f"{package_path}.ConcurrentOrchestration._start"),
        patch(f"{package_path}.ConcurrentAgentActor.register") as mock_agent_actor_register,
        patch(f"{package_path}.CollectionActor.register") as mock_collection_actor_register,
        patch.object(runtime, "add_subscription") as mock_add_subscription,
    ):
        orchestration = ConcurrentOrchestration(members=[agent_a, agent_b])
        await orchestration.invoke(task="test_message", runtime=runtime)

        assert mock_agent_actor_register.call_count == 2
        assert mock_collection_actor_register.call_count == 1
        assert mock_add_subscription.call_count == 2


async def test_invoke():
    """Test the invoke method of the ConcurrentOrchestration."""
    agent_a = MockAgent()
    agent_b = MockAgent()

    runtime = InProcessRuntime()
    runtime.start()

    try:
        orchestration = ConcurrentOrchestration(members=[agent_a, agent_b])
        orchestration_result = await orchestration.invoke(task="test_message", runtime=runtime)
        result = await orchestration_result.get(1.0)

        assert isinstance(orchestration_result, OrchestrationResult)
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(item, ChatMessageContent) for item in result)
    finally:
        await runtime.stop_when_idle()


async def test_invoke_with_response_callback():
    """Test the invoke method of the ConcurrentOrchestration with a response callback."""
    agent_a = MockAgent()
    agent_b = MockAgent()

    runtime = InProcessRuntime()
    runtime.start()

    responses: list[DefaultTypeAlias] = []
    try:
        orchestration = ConcurrentOrchestration(
            members=[agent_a, agent_b],
            agent_response_callback=lambda x: responses.append(x),
        )
        orchestration_result = await orchestration.invoke(task="test_message", runtime=runtime)
        await orchestration_result.get(1.0)

        assert len(responses) == 2
        assert all(isinstance(item, ChatMessageContent) for item in responses)
        assert all(item.content == "mock_response" for item in responses)
    finally:
        await runtime.stop_when_idle()


async def test_invoke_with_streaming_response_callback():
    """Test the invoke method of the ConcurrentOrchestration with a streaming response callback."""
    agent_a = MockAgent()
    agent_b = MockAgent()

    runtime = InProcessRuntime()
    runtime.start()

    responses: dict[str, list[StreamingChatMessageContent]] = {}
    try:
        orchestration = ConcurrentOrchestration(
            members=[agent_a, agent_b],
            streaming_agent_response_callback=lambda x, _: responses.setdefault(x.name, []).append(x),
        )
        orchestration_result = await orchestration.invoke(task="test_message", runtime=runtime)
        await orchestration_result.get(1.0)

        assert len(responses[agent_a.name]) == 2
        assert len(responses[agent_b.name]) == 2

        assert all(isinstance(item, StreamingChatMessageContent) for item in responses[agent_a.name])
        assert all(isinstance(item, StreamingChatMessageContent) for item in responses[agent_b.name])

        agent_a_response = sum(responses[agent_a.name][1:], responses[agent_a.name][0])
        assert agent_a_response.content == "mock_response"
        agent_b_response = sum(responses[agent_b.name][1:], responses[agent_b.name][0])
        assert agent_b_response.content == "mock_response"
    finally:
        await runtime.stop_when_idle()


@pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="Python 3.10 doesn't bound the original function provided to the wraps argument of the patch object.",
)
async def test_invoke_cancel_before_completion():
    """Test the invoke method of the ConcurrentOrchestration with cancellation before completion."""
    with (
        patch.object(MockAgent, "invoke_stream", wraps=MockAgent.invoke_stream, autospec=True) as mock_invoke_stream,
    ):
        agent_a = MockAgent()
        agent_b = MockAgent()

        runtime = InProcessRuntime()
        runtime.start()

        try:
            orchestration = ConcurrentOrchestration(members=[agent_a, agent_b])
            orchestration_result = await orchestration.invoke(task="test_message", runtime=runtime)

            # Cancel before the collection agent gets the responses
            await asyncio.sleep(0.05)
            orchestration_result.cancel()
        finally:
            await runtime.stop_when_idle()

        assert mock_invoke_stream.call_count == 2


async def test_invoke_cancel_after_completion():
    """Test the invoke method of the ConcurrentOrchestration with cancellation after completion."""
    agent_a = MockAgent()
    agent_b = MockAgent()

    runtime = InProcessRuntime()
    runtime.start()

    try:
        orchestration = ConcurrentOrchestration(members=[agent_a, agent_b])
        orchestration_result = await orchestration.invoke(task="test_message", runtime=runtime)

        # Wait for the orchestration to complete
        await orchestration_result.get(1.0)

        with pytest.raises(RuntimeError, match="The invocation has already been completed."):
            orchestration_result.cancel()
    finally:
        await runtime.stop_when_idle()


async def test_invoke_with_double_get_result():
    """Test the invoke method of the ConcurrentOrchestration with double get result."""
    agent_a = MockAgent()
    agent_b = MockAgent()

    runtime = InProcessRuntime()
    runtime.start()

    try:
        orchestration = ConcurrentOrchestration(members=[agent_a, agent_b])
        orchestration_result = await orchestration.invoke(task="test_message", runtime=runtime)

        # Get result before completion
        with pytest.raises(asyncio.TimeoutError):
            await orchestration_result.get(0.1)
        # The invocation should still be in progress and getting the result again should not raise an error
        result = await orchestration_result.get()

        assert isinstance(result, list)
        assert len(result) == 2
    finally:
        await runtime.stop_when_idle()
