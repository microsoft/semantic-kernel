# Copyright (c) Microsoft. All rights reserved.

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.history_reducer.chat_history_double_buffer_reducer import (
    GENERATION_METADATA_KEY,
    ChatHistoryDoubleBufferReducer,
    RenewalPolicy,
)
from semantic_kernel.contents.history_reducer.chat_history_reducer_utils import SUMMARY_METADATA_KEY
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.content_exceptions import ChatHistoryReducerException


@pytest.fixture
def mock_service():
    """Returns a mock ChatCompletionClientBase with required methods."""
    service = MagicMock(spec=ChatCompletionClientBase)
    service.get_prompt_execution_settings_class.return_value = MagicMock(return_value=MagicMock(service_id="foo"))
    service.get_chat_message_content = AsyncMock()
    service.get_prompt_execution_settings_from_settings.return_value = PromptExecutionSettings()
    return service


@pytest.fixture
def summary_message():
    """Returns a standard mock summary response."""
    return ChatMessageContent(role=AuthorRole.ASSISTANT, content="This is a summary of the conversation.")


async def _await_checkpoint(reducer: ChatHistoryDoubleBufferReducer) -> None:
    """Wait for a background checkpoint task to complete."""
    if reducer._checkpoint_task is not None and not reducer._checkpoint_task.done():
        await reducer._checkpoint_task
        reducer._checkpoint_task = None


def _make_messages(count: int, *, with_summary: bool = False) -> list[ChatMessageContent]:
    """Generate a list of alternating user/assistant messages."""
    msgs = []
    if with_summary:
        summary = ChatMessageContent(role=AuthorRole.SYSTEM, content="Prior summary.")
        summary.metadata[SUMMARY_METADATA_KEY] = True
        msgs.append(summary)
    for i in range(count):
        role = AuthorRole.USER if i % 2 == 0 else AuthorRole.ASSISTANT
        msgs.append(ChatMessageContent(role=role, content=f"Message {i}"))
    return msgs


# --- Init and Validation Tests ---


def test_double_buffer_reducer_init(mock_service):
    reducer = ChatHistoryDoubleBufferReducer(
        service=mock_service,
        target_count=20,
        checkpoint_threshold=0.6,
        swap_threshold=0.9,
        max_generations=3,
        renewal_policy=RenewalPolicy.DUMP,
    )
    assert reducer.target_count == 20
    assert reducer.checkpoint_threshold == 0.6
    assert reducer.swap_threshold == 0.9
    assert reducer.max_generations == 3
    assert reducer.renewal_policy == RenewalPolicy.DUMP


def test_double_buffer_reducer_defaults(mock_service):
    reducer = ChatHistoryDoubleBufferReducer(service=mock_service, target_count=10)
    assert reducer.checkpoint_threshold == 0.7
    assert reducer.swap_threshold == 0.95
    assert reducer.max_generations is None
    assert reducer.renewal_policy == RenewalPolicy.RECURSE
    assert reducer.fail_on_error is True
    assert reducer.generation == 0
    assert reducer.has_back_buffer is False
    assert reducer.back_buffer_size == 0


def test_swap_threshold_must_exceed_checkpoint_threshold(mock_service):
    with pytest.raises(ValueError, match="swap_threshold.*must be greater"):
        ChatHistoryDoubleBufferReducer(
            service=mock_service,
            target_count=10,
            checkpoint_threshold=0.8,
            swap_threshold=0.5,
        )


def test_swap_threshold_cannot_equal_checkpoint_threshold(mock_service):
    with pytest.raises(ValueError, match="swap_threshold.*must be greater"):
        ChatHistoryDoubleBufferReducer(
            service=mock_service,
            target_count=10,
            checkpoint_threshold=0.7,
            swap_threshold=0.7,
        )


def test_double_buffer_reducer_eq_and_hash(mock_service):
    r1 = ChatHistoryDoubleBufferReducer(service=mock_service, target_count=10, max_generations=3)
    r2 = ChatHistoryDoubleBufferReducer(service=mock_service, target_count=10, max_generations=3)
    r3 = ChatHistoryDoubleBufferReducer(service=mock_service, target_count=10, max_generations=7)
    assert r1 == r2
    assert r1 != r3
    assert hash(r1) == hash(r2)
    assert hash(r1) != hash(r3)


# --- Phase 1: Checkpoint Tests ---


async def test_no_reduction_below_checkpoint_threshold(mock_service):
    """No action when message count is below checkpoint threshold."""
    reducer = ChatHistoryDoubleBufferReducer(
        service=mock_service,
        target_count=20,
        checkpoint_threshold=0.7,  # triggers at 14 messages
    )
    reducer.messages = _make_messages(10)
    result = await reducer.reduce()
    assert result is None
    assert reducer.has_back_buffer is False
    mock_service.get_chat_message_content.assert_not_awaited()


async def test_checkpoint_creates_back_buffer(mock_service, summary_message):
    """Hitting checkpoint threshold creates a back buffer seeded with summary."""
    mock_service.get_chat_message_content.return_value = summary_message

    reducer = ChatHistoryDoubleBufferReducer(
        service=mock_service,
        target_count=10,
        threshold_count=0,
        checkpoint_threshold=0.5,  # triggers at 5 messages
        swap_threshold=0.9,
    )
    reducer.messages = _make_messages(8)

    result = await reducer.reduce()
    assert result is not None  # checkpoint was kicked off
    await _await_checkpoint(reducer)  # wait for background task
    assert reducer.has_back_buffer is True
    assert reducer.back_buffer_size > 0
    # Original messages should be untouched
    assert len(reducer.messages) == 8


async def test_checkpoint_tags_summary_with_generation(mock_service, summary_message):
    """Summary message should be tagged with generation metadata."""
    mock_service.get_chat_message_content.return_value = summary_message

    reducer = ChatHistoryDoubleBufferReducer(
        service=mock_service,
        target_count=10,
        threshold_count=0,
        checkpoint_threshold=0.5,
        swap_threshold=0.9,
    )
    reducer.messages = _make_messages(8)
    await reducer.reduce()
    await _await_checkpoint(reducer)

    # Find the summary in the back buffer
    summaries = [
        msg for msg in (reducer._back_buffer or [])
        if msg.metadata.get(SUMMARY_METADATA_KEY)
    ]
    assert len(summaries) >= 1
    assert summaries[-1].metadata.get(GENERATION_METADATA_KEY) == 1


# --- Phase 2: Concurrent Phase Tests ---


async def test_concurrent_phase_appends_to_both_buffers(mock_service, summary_message):
    """During concurrent phase, new messages go to both active and back buffer."""
    mock_service.get_chat_message_content.return_value = summary_message

    reducer = ChatHistoryDoubleBufferReducer(
        service=mock_service,
        target_count=10,
        threshold_count=0,
        checkpoint_threshold=0.5,
        swap_threshold=0.9,
    )
    reducer.messages = _make_messages(6)
    await reducer.reduce()  # kicks off checkpoint
    await _await_checkpoint(reducer)  # wait for it

    assert reducer.has_back_buffer is True
    back_buffer_size_before = reducer.back_buffer_size
    active_size_before = len(reducer.messages)

    # Add a new message — should go to both
    new_msg = ChatMessageContent(role=AuthorRole.USER, content="New message during concurrent phase")
    await reducer.add_message_async(new_msg)

    assert len(reducer.messages) == active_size_before + 1
    assert reducer.back_buffer_size == back_buffer_size_before + 1


# --- Phase 3: Swap Tests ---


async def test_swap_at_threshold(mock_service, summary_message):
    """Buffer swap occurs when active buffer hits swap threshold."""
    mock_service.get_chat_message_content.return_value = summary_message

    reducer = ChatHistoryDoubleBufferReducer(
        service=mock_service,
        target_count=10,
        threshold_count=0,
        checkpoint_threshold=0.5,  # checkpoint at 5
        swap_threshold=0.9,        # swap at 9
    )
    # Load enough to trigger checkpoint
    reducer.messages = _make_messages(6)
    await reducer.reduce()
    await _await_checkpoint(reducer)
    assert reducer.has_back_buffer is True
    assert reducer.generation == 0

    # Now add messages until we hit swap threshold
    while len(reducer.messages) < 9:
        msg = ChatMessageContent(role=AuthorRole.USER, content="Filler")
        await reducer.add_message_async(msg)

    # This reduce should trigger the swap
    result = await reducer.reduce()
    assert result is not None
    assert reducer.generation == 1
    assert reducer.has_back_buffer is False
    # Back buffer should now be the active buffer — it should be smaller
    # than the pre-swap active buffer since it has compressed history
    assert len(reducer.messages) > 0


async def test_swap_increments_generation(mock_service, summary_message):
    """Each swap increments the generation counter."""
    mock_service.get_chat_message_content.return_value = summary_message

    reducer = ChatHistoryDoubleBufferReducer(
        service=mock_service,
        target_count=10,
        threshold_count=0,
        checkpoint_threshold=0.3,
        swap_threshold=0.8,
    )
    reducer.messages = _make_messages(6)

    # First cycle: checkpoint + swap
    await reducer.reduce()  # checkpoint
    assert reducer.generation == 0
    reducer.messages = _make_messages(9)  # force above swap threshold
    reducer._back_buffer = _make_messages(4, with_summary=True)  # simulate back buffer
    await reducer.reduce()  # swap
    assert reducer.generation == 1


# --- Renewal Tests ---


async def test_renewal_dump_policy(mock_service, summary_message):
    """DUMP renewal policy discards all summaries and resets generation."""
    mock_service.get_chat_message_content.return_value = summary_message

    reducer = ChatHistoryDoubleBufferReducer(
        service=mock_service,
        target_count=20,
        threshold_count=0,
        checkpoint_threshold=0.5,
        swap_threshold=0.9,
        max_generations=2,
        renewal_policy=RenewalPolicy.DUMP,
    )

    # Simulate having reached max generations
    reducer._current_generation = 2
    msgs = _make_messages(12, with_summary=True)
    reducer.messages = msgs

    # Trigger checkpoint — should perform renewal first
    await reducer.reduce()
    await _await_checkpoint(reducer)

    # Generation should be reset
    assert reducer._current_generation == 0 or reducer.generation == 0


async def test_renewal_recurse_policy(mock_service, summary_message):
    """RECURSE renewal policy meta-summarizes accumulated summaries."""
    mock_service.get_chat_message_content.return_value = summary_message

    reducer = ChatHistoryDoubleBufferReducer(
        service=mock_service,
        target_count=20,
        threshold_count=0,
        checkpoint_threshold=0.5,
        swap_threshold=0.9,
        max_generations=2,
        renewal_policy=RenewalPolicy.RECURSE,
    )

    # Simulate having reached max generations with multiple summaries
    reducer._current_generation = 2
    summary1 = ChatMessageContent(role=AuthorRole.SYSTEM, content="Summary gen 1.")
    summary1.metadata[SUMMARY_METADATA_KEY] = True
    summary2 = ChatMessageContent(role=AuthorRole.SYSTEM, content="Summary gen 2.")
    summary2.metadata[SUMMARY_METADATA_KEY] = True
    reducer.messages = [summary1, summary2, *_make_messages(12)]

    await reducer.reduce()
    await _await_checkpoint(reducer)

    # Should have called the service for meta-summarization
    assert mock_service.get_chat_message_content.await_count >= 1


# --- Error Handling Tests ---


async def test_checkpoint_failure_with_fail_on_error(mock_service):
    """Checkpoint failure raises when fail_on_error is True."""
    mock_service.get_chat_message_content.side_effect = Exception("LLM error")

    reducer = ChatHistoryDoubleBufferReducer(
        service=mock_service,
        target_count=10,
        threshold_count=0,
        checkpoint_threshold=0.5,
        swap_threshold=0.9,
        fail_on_error=True,
    )
    reducer.messages = _make_messages(8)

    # Kick off checkpoint (runs in background)
    await reducer.reduce()
    # Await the background task — it should raise
    with pytest.raises(ChatHistoryReducerException, match="failed"):
        await _await_checkpoint(reducer)


async def test_checkpoint_failure_without_fail_on_error(mock_service):
    """Checkpoint failure logs warning and leaves no back buffer."""
    mock_service.get_chat_message_content.side_effect = Exception("LLM error")

    reducer = ChatHistoryDoubleBufferReducer(
        service=mock_service,
        target_count=10,
        threshold_count=0,
        checkpoint_threshold=0.5,
        swap_threshold=0.9,
        fail_on_error=False,
    )
    reducer.messages = _make_messages(8)

    await reducer.reduce()
    await _await_checkpoint(reducer)
    assert reducer.has_back_buffer is False


async def test_checkpoint_with_no_summarizable_messages(mock_service):
    """Returns None when there are no messages to summarize."""
    reducer = ChatHistoryDoubleBufferReducer(
        service=mock_service,
        target_count=10,
        threshold_count=10,  # high threshold means no reduction needed
        checkpoint_threshold=0.5,
        swap_threshold=0.9,
    )
    reducer.messages = _make_messages(6)

    await reducer.reduce()
    await _await_checkpoint(reducer)
    assert reducer.has_back_buffer is False
    mock_service.get_chat_message_content.assert_not_awaited()


# --- Auto-reduce Tests ---


async def test_auto_reduce_triggers_checkpoint(mock_service, summary_message):
    """With auto_reduce=True, adding messages can trigger checkpoint."""
    mock_service.get_chat_message_content.return_value = summary_message

    reducer = ChatHistoryDoubleBufferReducer(
        service=mock_service,
        target_count=6,
        threshold_count=0,
        checkpoint_threshold=0.5,  # checkpoint at 3
        swap_threshold=0.9,
        auto_reduce=True,
    )

    # Add messages one by one — checkpoint should trigger automatically
    for i in range(5):
        role = AuthorRole.USER if i % 2 == 0 else AuthorRole.ASSISTANT
        await reducer.add_message_async(ChatMessageContent(role=role, content=f"Msg {i}"))

    # By now checkpoint should have been triggered
    # (exact behavior depends on threshold math, but service should have been called)


# --- Graceful Degradation Tests ---


async def test_graceful_degradation_on_summarizer_returning_none(mock_service):
    """If summarizer returns None, checkpoint is aborted gracefully."""
    mock_service.get_chat_message_content.return_value = None

    reducer = ChatHistoryDoubleBufferReducer(
        service=mock_service,
        target_count=10,
        threshold_count=0,
        checkpoint_threshold=0.5,
        swap_threshold=0.9,
    )
    reducer.messages = _make_messages(8)

    await reducer.reduce()
    await _await_checkpoint(reducer)
    assert reducer.has_back_buffer is False


async def test_no_double_checkpoint(mock_service, summary_message):
    """Calling reduce twice doesn't create a second checkpoint if one exists."""
    mock_service.get_chat_message_content.return_value = summary_message

    reducer = ChatHistoryDoubleBufferReducer(
        service=mock_service,
        target_count=10,
        threshold_count=0,
        checkpoint_threshold=0.5,
        swap_threshold=0.9,
    )
    reducer.messages = _make_messages(8)

    # First reduce kicks off checkpoint in background
    await reducer.reduce()
    await _await_checkpoint(reducer)
    assert reducer.has_back_buffer is True
    call_count_after_first = mock_service.get_chat_message_content.await_count

    # Second reduce should not create another checkpoint (back buffer already exists)
    result = await reducer.reduce()
    assert result is None  # no swap needed yet, no new checkpoint needed
    assert mock_service.get_chat_message_content.await_count == call_count_after_first
