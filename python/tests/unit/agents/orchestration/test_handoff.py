# Copyright (c) Microsoft. All rights reserved.

import asyncio
import sys
from collections.abc import AsyncIterable, Awaitable, Callable
from unittest.mock import patch

import pytest

from semantic_kernel.agents.agent import Agent, AgentResponseItem, AgentThread
from semantic_kernel.agents.orchestration.handoffs import (
    HANDOFF_PLUGIN_NAME,
    HandoffAgentActor,
    HandoffOrchestration,
    OrchestrationHandoffs,
)
from semantic_kernel.agents.orchestration.orchestration_base import DefaultTypeAlias
from semantic_kernel.agents.runtime.in_process.in_process_runtime import InProcessRuntime
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel import Kernel
from tests.unit.agents.orchestration.conftest import MockAgent, MockRuntime

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover


class MockAgentWithHandoffFunctionCall(Agent):
    """A mock agent with handoff function call for testing purposes."""

    target_agent: Agent

    def __init__(self, target_agent: Agent):
        super().__init__(target_agent=target_agent)

    @override
    async def get_response(
        self,
        *,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        thread: AgentThread | None = None,
        kernel: Kernel | None = None,
        **kwargs,
    ) -> AgentResponseItem[ChatMessageContent]:
        pass

    @override
    async def invoke(
        self,
        *,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        thread: AgentThread | None = None,
        on_intermediate_message: Callable[[ChatMessageContent], Awaitable[None]] | None = None,
        **kwargs,
    ) -> AgentResponseItem[ChatMessageContent]:
        pass

    @override
    async def invoke_stream(
        self,
        *,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        thread: AgentThread | None = None,
        on_intermediate_message: Callable[[ChatMessageContent], Awaitable[None]] | None = None,
        kernel: Kernel | None = None,
        **kwargs,
    ) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:
        """Simulate streaming response from the agent."""
        # Simulate some processing time
        await asyncio.sleep(0.1)
        await kernel.invoke_function_call(
            function_call=FunctionCallContent(
                function_name=f"transfer_to_{self.target_agent.name}",
                plugin_name=HANDOFF_PLUGIN_NAME,
                call_id="test_call_id",
                id="test_id",
            ),
            chat_history=ChatHistory(),
        )

        # Do not yield any messages, as the agent doesn't yield any tool related messages from the streaming API.
        # Nevertheless, the method needs have a `yield` code path to satisfy the AsyncIterable interface.
        if False:
            yield


class MockAgentWithCompleteTaskFunctionCall(Agent):
    """A mock agent with complete_task function call for testing purposes."""

    @override
    async def get_response(
        self,
        *,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        thread: AgentThread | None = None,
        kernel: Kernel | None = None,
        **kwargs,
    ) -> AgentResponseItem[ChatMessageContent]:
        pass

    @override
    async def invoke(
        self,
        *,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        thread: AgentThread | None = None,
        on_intermediate_message: Callable[[ChatMessageContent], Awaitable[None]] | None = None,
        **kwargs,
    ) -> AgentResponseItem[ChatMessageContent]:
        pass

    @override
    async def invoke_stream(
        self,
        *,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        thread: AgentThread | None = None,
        on_intermediate_message: Callable[[ChatMessageContent], Awaitable[None]] | None = None,
        kernel: Kernel | None = None,
        **kwargs,
    ) -> AsyncIterable[AgentResponseItem[StreamingChatMessageContent]]:
        """Simulate streaming response from the agent."""
        # Simulate some processing time
        await asyncio.sleep(0.1)
        await kernel.invoke_function_call(
            function_call=FunctionCallContent(
                function_name="complete_task",
                plugin_name=HANDOFF_PLUGIN_NAME,
                call_id="test_call_id",
                id="test_id",
                arguments={"task_summary": "test_summary"},
            ),
            chat_history=ChatHistory(),
        )

        # Do not yield any messages, as the agent doesn't yield any tool related messages from the streaming API.
        # Nevertheless, the method needs have a `yield` code path to satisfy the AsyncIterable interface.
        if False:
            yield


# region HandoffOrchestration


def test_init_without_handoffs():
    """Test the initialization of HandoffOrchestration without handoffs."""
    agent_a = MockAgent()
    agent_b = MockAgent()

    with pytest.raises(ValueError):
        HandoffOrchestration(members=[agent_a, agent_b], handoffs={})


def test_init_with_invalid_handoff():
    """Test the initialization of HandoffOrchestration with invalid handoff."""
    agent_a = MockAgent()
    agent_b = MockAgent()

    # Invalid handoff agent name
    with pytest.raises(ValueError):
        HandoffOrchestration(
            members=[agent_a, agent_b],
            handoffs={
                agent_a.name: {agent_b.name: "test", "invalid_agent_name": "test"},
                agent_b.name: {agent_a.name: "test"},
            },
        )

    # Invalid handoff agent name (not in members)
    with pytest.raises(ValueError):
        HandoffOrchestration(
            members=[agent_a, agent_b],
            handoffs={
                "invalid_agent_name": {agent_b.name: "test"},
                agent_b.name: {agent_a.name: "test"},
            },
        )

    # Cannot handoff to self
    with pytest.raises(ValueError):
        HandoffOrchestration(
            members=[agent_a, agent_b],
            handoffs={
                agent_a.name: {agent_a.name: "test"},
                agent_b.name: {agent_a.name: "test"},
            },
        )


def test_init_with_duplicate_handoffs():
    """Test the initialization of HandoffOrchestration with duplicate handoffs."""
    agent_a = MockAgent()
    agent_b = MockAgent()

    # Uniqueness guarantee
    orchestration = HandoffOrchestration(
        members=[agent_a, agent_b],
        handoffs={
            agent_a.name: {agent_b.name: "test 1", agent_b.name: "test 2"},
        },
    )

    assert len(orchestration._handoffs[agent_a.name]) == 1


def test_init_with_dictionary_handoffs():
    """Test the initialization of HandoffOrchestration with dictionary handoffs."""
    agent_a = MockAgent()
    agent_b = MockAgent()

    orchestration_handoffs = OrchestrationHandoffs(
        {
            agent_a.name: {agent_b.name: "test 1"},
            agent_b.name: {agent_a.name: "test 2"},
        },
    )

    assert len(orchestration_handoffs) == 2
    for handoff_agent_name, handoff_description in orchestration_handoffs[agent_a.name].items():
        assert handoff_agent_name == agent_b.name
        assert handoff_description == "test 1"

    for handoff_agent_name, handoff_description in orchestration_handoffs[agent_b.name].items():
        assert handoff_agent_name == agent_a.name
        assert handoff_description == "test 2"


def test_orchestration_handoff_add():
    """Test the add method of the OrchestrationHandoffs."""
    agent_a = MockAgent()
    agent_b = MockAgent()

    orchestration_handoffs = OrchestrationHandoffs().add(agent_a, agent_b).add(agent_b, agent_a)

    assert isinstance(orchestration_handoffs, OrchestrationHandoffs)
    assert len(orchestration_handoffs) == 2
    assert len(orchestration_handoffs[agent_a.name]) == 1
    assert len(orchestration_handoffs[agent_b.name]) == 1
    for handoff_agent_name, handoff_description in orchestration_handoffs[agent_a.name].items():
        assert handoff_agent_name == agent_b.name
        assert handoff_description == ""
    for handoff_agent_name, handoff_description in orchestration_handoffs[agent_b.name].items():
        assert handoff_agent_name == agent_a.name
        assert handoff_description == ""


def test_orchestration_handoff_add_many():
    """Test the add_many method of the OrchestrationHandoffs."""
    agent_a = MockAgent(description="agent_a")
    agent_b = MockAgent(description="agent_b")
    agent_c = MockAgent(description="agent_c")

    # Case 1: Agent instance as source and dictionary as handoffs
    orchestration_handoffs = OrchestrationHandoffs().add_many(
        agent_a,
        {agent_b.name: "test 1", agent_c.name: "test 2"},
    )

    assert isinstance(orchestration_handoffs, OrchestrationHandoffs)
    assert len(orchestration_handoffs) == 1
    assert len(orchestration_handoffs[agent_a.name]) == 2
    for handoff_agent_name, handoff_description in orchestration_handoffs[agent_a.name].items():
        assert handoff_agent_name in [agent_b.name, agent_c.name]
        assert handoff_description in ["test 1", "test 2"]

    # Case 2: Agent name as source and list of agents as handoffs
    orchestration_handoffs = OrchestrationHandoffs().add_many(
        agent_a.name,
        {agent_b.name: "test 1", agent_c.name: "test 2"},
    )

    assert isinstance(orchestration_handoffs, OrchestrationHandoffs)
    assert len(orchestration_handoffs) == 1
    assert len(orchestration_handoffs[agent_a.name]) == 2
    for handoff_agent_name, handoff_description in orchestration_handoffs[agent_a.name].items():
        assert handoff_agent_name in [agent_b.name, agent_c.name]
        assert handoff_description in ["test 1", "test 2"]

    # Case 3: Agent instance as source and list of agents as handoffs
    orchestration_handoffs = OrchestrationHandoffs().add_many(agent_a, [agent_b, agent_c])
    assert isinstance(orchestration_handoffs, OrchestrationHandoffs)
    assert len(orchestration_handoffs) == 1
    assert len(orchestration_handoffs[agent_a.name]) == 2
    for handoff_agent_name, handoff_description in orchestration_handoffs[agent_a.name].items():
        assert handoff_agent_name in [agent_b.name, agent_c.name]
        assert handoff_description in [agent_b.description, agent_c.description]

    # Case 4: Agent name as source and list of agent names as handoffs
    orchestration_handoffs = OrchestrationHandoffs().add_many(agent_a.name, [agent_b.name, agent_c.name])
    assert isinstance(orchestration_handoffs, OrchestrationHandoffs)
    assert len(orchestration_handoffs) == 1
    assert len(orchestration_handoffs[agent_a.name]) == 2
    for handoff_agent_name, handoff_description in orchestration_handoffs[agent_a.name].items():
        assert handoff_agent_name in [agent_b.name, agent_c.name]
        assert handoff_description == ""


async def test_prepare():
    """Test the prepare method of the HandoffOrchestration."""
    agent_a = MockAgent()
    agent_b = MockAgent()
    agent_c = MockAgent()

    runtime = MockRuntime()

    package_path = "semantic_kernel.agents.orchestration.handoffs"
    with (
        patch(f"{package_path}.HandoffOrchestration._start"),
        patch(f"{package_path}.HandoffAgentActor.register") as mock_agent_actor_register,
        patch.object(runtime, "add_subscription") as mock_add_subscription,
    ):
        orchestration = HandoffOrchestration(
            members=[agent_a, agent_b, agent_c],
            handoffs={
                agent_a.name: {agent_b.name: "test"},
                agent_b.name: {agent_c.name: "test"},
                agent_c.name: {agent_a.name: "test"},
            },
        )
        await orchestration.invoke(task="test_message", runtime=runtime)

        assert mock_agent_actor_register.call_count == 3
        assert mock_add_subscription.call_count == 3


@pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="Python 3.10 doesn't bound the original function provided to the wraps argument of the patch object.",
)
async def test_invoke():
    """Test the prepare method of the HandoffOrchestration."""
    with (
        patch.object(HandoffAgentActor, "__init__", wraps=HandoffAgentActor.__init__, autospec=True) as mock_init,
        patch.object(MockAgent, "invoke_stream", wraps=MockAgent.invoke_stream, autospec=True) as mock_invoke_stream,
    ):
        agent_a = MockAgent()
        agent_b = MockAgent()
        agent_c = MockAgent()

        runtime = InProcessRuntime()
        runtime.start()

        try:
            orchestration = HandoffOrchestration(
                members=[agent_a, agent_b, agent_c],
                handoffs={
                    agent_a.name: {agent_b.name: "test", agent_c.name: "test"},
                    agent_b.name: {agent_a.name: "test"},
                },
            )
            orchestration_result = await orchestration.invoke(task="test_message", runtime=runtime)
            await orchestration_result.get()

            assert mock_init.call_args_list[0][0][3] == {agent_b.name: "test", agent_c.name: "test"}
            assert isinstance(mock_invoke_stream.call_args_list[0][1]["kernel"], Kernel)
            kernel = mock_invoke_stream.call_args_list[0][1]["kernel"]
            assert HANDOFF_PLUGIN_NAME in kernel.plugins
            assert (
                len(kernel.plugins[HANDOFF_PLUGIN_NAME].functions) == 3
            )  # two handoff functions + complete task function
            # The kernel in the agent should not be modified
            assert len(agent_a.kernel.plugins) == 0
            assert len(agent_b.kernel.plugins) == 0
            assert len(agent_c.kernel.plugins) == 0
        finally:
            await runtime.stop_when_idle()


@pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="Python 3.10 doesn't bound the original function provided to the wraps argument of the patch object.",
)
async def test_invoke_with_list():
    """Test the invoke method of the HandoffOrchestration with a list of messages."""
    with (
        patch.object(MockAgent, "invoke_stream", wraps=MockAgent.invoke_stream, autospec=True) as mock_invoke_stream,
    ):
        agent_a = MockAgent()
        agent_b = MockAgent()

        runtime = InProcessRuntime()
        runtime.start()

        messages = [
            ChatMessageContent(role=AuthorRole.USER, content="test_message_1"),
            ChatMessageContent(role=AuthorRole.USER, content="test_message_2"),
        ]

        try:
            orchestration = HandoffOrchestration(
                members=[agent_a, agent_b],
                handoffs={agent_a.name: {agent_b.name: "test"}},
            )
            orchestration_result = await orchestration.invoke(task=messages, runtime=runtime)
            await orchestration_result.get()
        finally:
            await runtime.stop_when_idle()

        assert mock_invoke_stream.call_count == 1
        # Two messages
        assert len(mock_invoke_stream.call_args_list[0][1]["messages"]) == 2
        # The kernel in the agent should not be modified
        assert len(agent_a.kernel.plugins) == 0
        assert len(agent_b.kernel.plugins) == 0


async def test_invoke_with_response_callback():
    """Test the invoke method of the HandoffOrchestration with a response callback."""
    agent_a = MockAgent()
    agent_b = MockAgent()

    runtime = InProcessRuntime()
    runtime.start()

    responses: list[DefaultTypeAlias] = []
    try:
        orchestration = HandoffOrchestration(
            members=[agent_a, agent_b],
            handoffs={agent_a.name: {agent_b.name: "test"}},
            agent_response_callback=lambda x: responses.append(x),
        )
        orchestration_result = await orchestration.invoke(task="test_message", runtime=runtime)
        await orchestration_result.get(1.0)
    finally:
        await runtime.stop_when_idle()

    assert len(responses) == 1
    assert all(isinstance(item, ChatMessageContent) for item in responses)
    assert all(item.content == "mock_response" for item in responses)
    # The kernel in the agent should not be modified
    assert len(agent_a.kernel.plugins) == 0
    assert len(agent_b.kernel.plugins) == 0


async def test_invoke_with_streaming_response_callback():
    """Test the invoke method of the HandoffOrchestration with a streaming response callback."""
    agent_a = MockAgent()
    agent_b = MockAgent()

    runtime = InProcessRuntime()
    runtime.start()

    responses: dict[str, list[StreamingChatMessageContent]] = {}
    try:
        orchestration = HandoffOrchestration(
            members=[agent_a, agent_b],
            handoffs={agent_a.name: {agent_b.name: "test"}},
            streaming_agent_response_callback=lambda x, _: responses.setdefault(x.name, []).append(x),
        )
        orchestration_result = await orchestration.invoke(task="test_message", runtime=runtime)
        await orchestration_result.get(1.0)
    finally:
        await runtime.stop_when_idle()

    assert len(responses[agent_a.name]) == 2
    assert all(isinstance(item, StreamingChatMessageContent) for item in responses[agent_a.name])
    agent_a_response = sum(responses[agent_a.name][1:], responses[agent_a.name][0])
    assert agent_a_response.content == "mock_response"

    # Agent B was not invoked, so it should not have any responses
    assert agent_b.name not in responses or len(responses[agent_b.name]) == 0

    # The kernel in the agent should not be modified
    assert len(agent_a.kernel.plugins) == 0
    assert len(agent_b.kernel.plugins) == 0


@pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="Python 3.10 doesn't bound the original function provided to the wraps argument of the patch object.",
)
async def test_invoke_with_human_response_function():
    """Test the invoke method of the HandoffOrchestration with a human response function."""
    complete_task_agent_instance = MockAgentWithCompleteTaskFunctionCall()
    normal_agent_instance = MockAgent()
    call_sequence = iter([normal_agent_instance.invoke_stream, complete_task_agent_instance.invoke_stream])

    user_input_count = 0

    def human_response_function() -> ChatMessageContent:
        # Simulate user input
        nonlocal user_input_count
        user_input_count += 1
        return ChatMessageContent(role=AuthorRole.USER, content="user_input")

    with (
        patch.object(MockAgent, "invoke_stream") as mock_invoke_stream,
    ):
        mock_invoke_stream.side_effect = lambda *args, **kwargs: next(call_sequence)(*args, **kwargs)

        agent_a = MockAgent(name="agent_a")
        agent_b = MockAgent(name="agent_b")

        runtime = InProcessRuntime()
        runtime.start()

        try:
            orchestration = HandoffOrchestration(
                members=[agent_a, agent_b],
                handoffs={agent_a.name: {agent_b.name: "test"}},
                human_response_function=human_response_function,
            )
            orchestration_result = await orchestration.invoke(task="test_message", runtime=runtime)
            await orchestration_result.get(1.0)
        finally:
            await runtime.stop_when_idle()

        assert user_input_count == 1


@pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="Python 3.10 doesn't bound the original function provided to the wraps argument of the patch object.",
)
async def test_invoke_with_handoff_function_call():
    """Test the invoke method of the HandoffOrchestration with a handoff function call."""
    agent_b = MockAgent()
    agent_a = MockAgentWithHandoffFunctionCall(agent_b)

    with (
        patch.object(
            HandoffAgentActor, "_handoff_to_agent", wraps=HandoffAgentActor._handoff_to_agent, autospec=True
        ) as mock_handoff_to_agent,
    ):
        runtime = InProcessRuntime()
        runtime.start()

        try:
            orchestration = HandoffOrchestration(
                members=[agent_a, agent_b],
                handoffs={agent_a.name: {agent_b.name: "test"}},
            )
            orchestration_result = await orchestration.invoke(task="test_message", runtime=runtime)
            await orchestration_result.get()
        finally:
            await runtime.stop_when_idle()

        assert mock_handoff_to_agent.call_count == 1
        assert mock_handoff_to_agent.call_args_list[0][0][1] == agent_b.name
        # The kernel in the agent should not be modified
        assert len(agent_a.kernel.plugins) == 0
        assert len(agent_b.kernel.plugins) == 0


@pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="Python 3.10 doesn't bound the original function provided to the wraps argument of the patch object.",
)
async def test_invoke_cancel_before_completion():
    """Test the invoke method of the HandoffOrchestration with cancellation before completion."""
    with (
        patch.object(MockAgent, "invoke_stream", wraps=MockAgent.invoke_stream, autospec=True) as mock_invoke_stream,
    ):
        agent_a = MockAgent()
        agent_b = MockAgent()

        runtime = InProcessRuntime()
        runtime.start()

        try:
            orchestration = HandoffOrchestration(
                members=[agent_a, agent_b],
                handoffs={agent_a.name: {agent_b.name: "test"}},
            )
            orchestration_result = await orchestration.invoke(task="test_message", runtime=runtime)

            # Cancel before first agent completes
            await asyncio.sleep(0.05)
            orchestration_result.cancel()
        finally:
            await runtime.stop_when_idle()

        assert mock_invoke_stream.call_count == 1


async def test_invoke_cancel_after_completion():
    """Test the invoke method of the HandoffOrchestration with cancellation after completion."""
    agent_a = MockAgent()
    agent_b = MockAgent()

    runtime = InProcessRuntime()
    runtime.start()

    try:
        orchestration = HandoffOrchestration(
            members=[agent_a, agent_b],
            handoffs={agent_a.name: {agent_b.name: "test"}},
        )

        orchestration_result = await orchestration.invoke(task="test_message", runtime=runtime)

        # Wait for the orchestration to complete
        await orchestration_result.get(1.0)

        with pytest.raises(RuntimeError, match="The invocation has already been completed."):
            orchestration_result.cancel()
    finally:
        await runtime.stop_when_idle()


# endregion
