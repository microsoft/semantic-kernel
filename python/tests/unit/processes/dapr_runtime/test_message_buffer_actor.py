# Copyright (c) Microsoft. All rights reserved.

import asyncio
from unittest.mock import AsyncMock

import pytest
from dapr.actor.id import ActorId
from dapr.actor.runtime._type_information import ActorTypeInformation
from dapr.actor.runtime.context import ActorRuntimeContext
from dapr.serializers import DefaultJSONSerializer

from semantic_kernel.processes.dapr_runtime.actors.actor_state_key import ActorStateKeys
from semantic_kernel.processes.dapr_runtime.actors.message_buffer_actor import MessageBufferActor


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
    actor_type_info = ActorTypeInformation.create(MessageBufferActor)

    message_serializer = DefaultJSONSerializer()
    state_serializer = DefaultJSONSerializer()

    mock_actor_client = AsyncMock()

    mock_state_manager = AsyncMock()
    mock_state_manager.try_get_state.return_value = (True, [])
    mock_state_manager.try_add_state = AsyncMock()
    mock_state_manager.save_state = AsyncMock()

    runtime_context = ActorRuntimeContext(
        actor_type_info=actor_type_info,
        message_serializer=message_serializer,
        state_serializer=state_serializer,
        actor_client=mock_actor_client,
    )

    actor = MessageBufferActor(runtime_context, actor_id)
    actor._state_manager = mock_state_manager

    _run(actor._on_activate())
    return actor


def test_enqueue(actor_context):
    _run(actor_context.enqueue('{"event": "test_event"}'))
    queue_list = list(actor_context.queue.queue)
    assert queue_list == ['{"event": "test_event"}']

    actor_context._state_manager.try_add_state.assert_called_with(
        ActorStateKeys.MessageQueueState.value, ['{"event": "test_event"}']
    )
    actor_context._state_manager.save_state.assert_called_once()


def test_dequeue_all(actor_context):
    _run(actor_context.enqueue('{"event": "event1"}'))
    _run(actor_context.enqueue('{"event": "event2"}'))

    actor_context._state_manager.reset_mock()

    messages = _run(actor_context.dequeue_all())
    assert messages == ['{"event": "event1"}', '{"event": "event2"}']
    assert actor_context.queue.empty()

    actor_context._state_manager.try_add_state.assert_called_with(ActorStateKeys.MessageQueueState.value, "[]")
    actor_context._state_manager.save_state.assert_called_once()


def test_on_activate_with_existing_state(actor_context):
    actor_context._state_manager.try_get_state.return_value = (True, ['{"event": "event1"}', '{"event": "event2"}'])

    new_actor = MessageBufferActor(actor_context.runtime_ctx, actor_context.id)
    new_actor._state_manager = actor_context._state_manager
    _run(new_actor._on_activate())

    queue_list = list(new_actor.queue.queue)
    assert queue_list == ['{"event": "event1"}', '{"event": "event2"}']


def test_on_activate_with_no_existing_state(actor_context):
    actor_context._state_manager.try_get_state.return_value = (False, None)

    new_actor = MessageBufferActor(actor_context.runtime_ctx, actor_context.id)
    new_actor._state_manager = actor_context._state_manager
    _run(new_actor._on_activate())

    assert new_actor.queue.empty()
