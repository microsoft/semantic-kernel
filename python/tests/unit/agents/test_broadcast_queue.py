# Copyright (c) Microsoft. All rights reserved.

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.agents.group_chat.broadcast_queue import BroadcastQueue, ChannelReference, QueueReference
from semantic_kernel.contents.chat_message_content import ChatMessageContent


@pytest.fixture
def channel_ref():
    """Fixture that provides a mock ChannelReference."""
    mock_channel = AsyncMock(spec=AgentChannel)
    return ChannelReference(channel=mock_channel, hash="test-hash")


@pytest.fixture
def message():
    """Fixture that provides a mock ChatMessageContent."""
    return MagicMock(spec=ChatMessageContent)


# region QueueReference Tests


def test_queue_reference_is_empty_true():
    queue_ref = QueueReference()
    assert queue_ref.is_empty is True


def test_queue_reference_is_empty_false():
    queue_ref = QueueReference()
    queue_ref.queue.append(MagicMock())
    assert queue_ref.is_empty is False


# endregion

# region BroadcastQueue Tests


async def test_enqueue_new_channel(channel_ref, message):
    broadcast_queue = BroadcastQueue()

    await broadcast_queue.enqueue([channel_ref], [message])

    assert channel_ref.hash in broadcast_queue.queues
    queue_ref = broadcast_queue.queues[channel_ref.hash]
    assert queue_ref.queue[0] == [message]
    assert queue_ref.receive_task is not None
    assert not queue_ref.receive_task.done()


async def test_enqueue_existing_channel(channel_ref, message):
    broadcast_queue = BroadcastQueue()

    await broadcast_queue.enqueue([channel_ref], [message])

    await broadcast_queue.enqueue([channel_ref], [message])

    queue_ref = broadcast_queue.queues[channel_ref.hash]
    assert len(queue_ref.queue) == 2
    assert queue_ref.queue[1] == [message]
    assert queue_ref.receive_task is not None
    assert not queue_ref.receive_task.done()


async def test_ensure_synchronized_channel_empty(channel_ref):
    broadcast_queue = BroadcastQueue()

    await broadcast_queue.ensure_synchronized(channel_ref)
    assert channel_ref.hash not in broadcast_queue.queues


async def test_ensure_synchronized_with_messages(channel_ref, message):
    broadcast_queue = BroadcastQueue()

    await broadcast_queue.enqueue([channel_ref], [message])

    await broadcast_queue.ensure_synchronized(channel_ref)

    queue_ref = broadcast_queue.queues[channel_ref.hash]
    assert queue_ref.is_empty is True


async def test_ensure_synchronized_with_failure(channel_ref, message):
    broadcast_queue = BroadcastQueue()

    await broadcast_queue.enqueue([channel_ref], [message])

    queue_ref = broadcast_queue.queues[channel_ref.hash]
    queue_ref.receive_failure = Exception("Simulated failure")

    with pytest.raises(Exception, match="Unexpected failure broadcasting to channel"):
        await broadcast_queue.ensure_synchronized(channel_ref)

    assert queue_ref.receive_failure is None


async def test_ensure_synchronized_creates_new_task(channel_ref, message):
    broadcast_queue = BroadcastQueue()

    await broadcast_queue.enqueue([channel_ref], [message])

    queue_ref = broadcast_queue.queues[channel_ref.hash]

    queue_ref.receive_task = None

    with patch(
        "semantic_kernel.agents.group_chat.broadcast_queue.BroadcastQueue.receive", new_callable=AsyncMock
    ) as mock_receive:
        mock_receive.return_value = await asyncio.sleep(0.1)

        await broadcast_queue.ensure_synchronized(channel_ref)

        assert queue_ref.receive_task is None


async def test_receive_processes_queue(channel_ref, message):
    broadcast_queue = BroadcastQueue()

    await broadcast_queue.enqueue([channel_ref], [message])

    queue_ref = broadcast_queue.queues[channel_ref.hash]

    await broadcast_queue.receive(channel_ref, queue_ref)

    assert queue_ref.is_empty is True

    assert channel_ref.channel.receive.await_count >= 1
    channel_ref.channel.receive.assert_any_await([message])


async def test_receive_handles_failure(channel_ref, message):
    broadcast_queue = BroadcastQueue()

    await broadcast_queue.enqueue([channel_ref], [message])

    channel_ref.channel.receive.side_effect = Exception("Simulated failure")

    queue_ref = broadcast_queue.queues[channel_ref.hash]

    await broadcast_queue.receive(channel_ref, queue_ref)

    assert queue_ref.receive_failure is not None
    assert str(queue_ref.receive_failure) == "Simulated failure"


async def test_receive_breaks_when_queue_is_empty(channel_ref, message):
    broadcast_queue = BroadcastQueue()

    await broadcast_queue.enqueue([channel_ref], [message])

    queue_ref = broadcast_queue.queues[channel_ref.hash]

    assert not queue_ref.is_empty

    channel_ref.channel.receive = AsyncMock()

    queue_ref.queue.clear()

    await broadcast_queue.receive(channel_ref, queue_ref)

    channel_ref.channel.receive.assert_not_awaited()

    assert queue_ref.is_empty


# endregion
