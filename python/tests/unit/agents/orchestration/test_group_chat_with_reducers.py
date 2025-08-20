# Copyright (c) Microsoft. All rights reserved.

import sys

from semantic_kernel.agents.orchestration.group_chat import (
    GroupChatOrchestration,
    RoundRobinGroupChatManager,
)
from semantic_kernel.agents.runtime.in_process.in_process_runtime import InProcessRuntime
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.history_reducer.chat_history_truncation_reducer import ChatHistoryTruncationReducer
from tests.unit.agents.orchestration.conftest import MockAgent

if sys.version_info >= (3, 12):
    pass  # pragma: no cover
else:
    pass  # pragma: no cover


# region Tests with ChatHistoryTruncationReducer


async def test_group_chat_with_chat_history_parameter():
    """Test GroupChatOrchestration accepts chat_history parameter."""
    agent = MockAgent(name="TestAgent", description="Test agent")
    chat_history = ChatHistory()

    # Should not raise an error
    orchestration = GroupChatOrchestration(
        members=[agent], manager=RoundRobinGroupChatManager(), chat_history=chat_history
    )

    assert orchestration._chat_history is chat_history


async def test_group_chat_with_truncation_reducer():
    """Test GroupChatOrchestration with ChatHistoryTruncationReducer."""
    agent = MockAgent(name="TestAgent", description="Test agent")

    # Create truncation reducer that keeps only 2 messages
    reducer = ChatHistoryTruncationReducer(target_count=2, threshold_count=0, auto_reduce=True)

    runtime = InProcessRuntime()
    runtime.start()

    try:
        orchestration = GroupChatOrchestration(
            members=[agent], manager=RoundRobinGroupChatManager(max_rounds=3), chat_history=reducer
        )

        orchestration_result = await orchestration.invoke(task="Test message", runtime=runtime)
        await orchestration_result.get(timeout=1.0)

        # Verify the reducer was used and has messages
        assert len(reducer.messages) > 0, "Reducer should have received messages"

        # Verify truncation is working - should not exceed target_count + threshold_count + buffer
        # (The exact count may vary due to "transfer" messages and timing)
        assert len(reducer.messages) <= 5, "Reducer should limit message count"

    finally:
        await runtime.stop_when_idle()


async def test_group_chat_fallback_to_regular_chat_history():
    """Test that GroupChat falls back to add_message for regular ChatHistory."""
    agent = MockAgent(name="TestAgent", description="Test agent")

    # Use regular ChatHistory (no add_message_async method)
    regular_history = ChatHistory()

    runtime = InProcessRuntime()
    runtime.start()

    try:
        # Should work without errors
        orchestration = GroupChatOrchestration(
            members=[agent], manager=RoundRobinGroupChatManager(max_rounds=1), chat_history=regular_history
        )

        orchestration_result = await orchestration.invoke(task="Test message", runtime=runtime)
        await orchestration_result.get(timeout=1.0)

        # Verify messages were added to history
        assert len(regular_history.messages) > 0, "Messages should be added to regular ChatHistory"

    finally:
        await runtime.stop_when_idle()


async def test_group_chat_no_chat_history_parameter():
    """Test GroupChatOrchestration works when no chat_history provided."""
    agent = MockAgent(name="TestAgent", description="Test agent")

    orchestration = GroupChatOrchestration(members=[agent], manager=RoundRobinGroupChatManager())

    # Should not set chat_history in constructor when None provided
    assert orchestration._chat_history is None


async def test_empty_reducer_not_replaced_by_default_history():
    """Test that empty ChatHistoryReducer instances are not replaced by default ChatHistory.

    This is a regression test for the bug where empty reducers evaluated to False
    and were replaced by ChatHistory() due to the 'chat_history or ChatHistory()' pattern.
    """
    agent = MockAgent(name="TestAgent", description="Test agent")

    # Create empty reducer (should evaluate to False in boolean context but still be used)
    empty_reducer = ChatHistoryTruncationReducer(target_count=5, threshold_count=0, auto_reduce=True)

    # Verify it's empty and evaluates to False initially
    assert len(empty_reducer.messages) == 0
    assert bool(empty_reducer) is False

    runtime = InProcessRuntime()
    runtime.start()

    try:
        orchestration = GroupChatOrchestration(
            members=[agent], manager=RoundRobinGroupChatManager(max_rounds=1), chat_history=empty_reducer
        )

        orchestration_result = await orchestration.invoke(task="Test message", runtime=runtime)
        await orchestration_result.get(timeout=1.0)

        # Verify messages were added to our reducer (not a default ChatHistory)
        assert len(empty_reducer.messages) > 0, "Messages should be added to the reducer instance"

        # Verify we can access reducer-specific functionality (proves it's our reducer)
        assert hasattr(empty_reducer, "auto_reduce"), "Should still be our reducer instance"
        assert empty_reducer.auto_reduce is True, "Should have reducer-specific properties"
        assert empty_reducer.target_count == 5, "Should have our original target_count"

    finally:
        await runtime.stop_when_idle()


# endregion Tests with ChatHistoryTruncationReducer
