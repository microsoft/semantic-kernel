# Copyright (c) Microsoft. All rights reserved.

import asyncio
from unittest.mock import AsyncMock

import pytest
from dapr.actor.id import ActorId
from dapr.actor.runtime._type_information import ActorTypeInformation
from dapr.actor.runtime.context import ActorRuntimeContext
from dapr.serializers import DefaultJSONSerializer

from semantic_kernel.processes.dapr_runtime.actors.event_buffer_actor import EventBufferActor


def _run(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@pytest.fixture
def actor_context():
    actor_id = ActorId("test_actor")
    actor_type_info = ActorTypeInformation.create(EventBufferActor)

    message_serializer = DefaultJSONSerializer()
    state_serializer = DefaultJSONSerializer()

    mock_actor_client = AsyncMock()

    runtime_context = ActorRuntimeContext(
        actor_type_info=actor_type_info,
        message_serializer=message_serializer,
        state_serializer=state_serializer,
        actor_client=mock_actor_client,
    )

    actor = EventBufferActor(runtime_context, actor_id)

    _run(actor._on_activate())
    return actor


def test_enqueue(actor_context):
    _run(actor_context.enqueue('{"event": "test_event"}'))
    queue_list = list(actor_context.queue.queue)
    assert queue_list == ['{"event": "test_event"}']


def test_dequeue_all(actor_context):
    _run(actor_context.enqueue('{"event": "event1"}'))
    _run(actor_context.enqueue('{"event": "event2"}'))
    messages = _run(actor_context.dequeue_all())
    assert messages == ['{"event": "event1"}', '{"event": "event2"}']
    assert actor_context.queue.empty()


def test_on_activate(actor_context):
    new_actor = EventBufferActor(actor_context.runtime_ctx, actor_context.id)
    _run(new_actor._on_activate())
    assert new_actor.queue.empty()
