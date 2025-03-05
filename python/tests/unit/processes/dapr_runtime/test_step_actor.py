# Copyright (c) Microsoft. All rights reserved.

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dapr.actor import ActorId

from semantic_kernel.processes.dapr_runtime.actors.step_actor import StepActor
from semantic_kernel.processes.dapr_runtime.dapr_step_info import DaprStepInfo
from semantic_kernel.processes.kernel_process.kernel_process_step_state import KernelProcessStepState
from semantic_kernel.processes.process_message import ProcessMessage


@pytest.fixture
def actor_context():
    ctx = MagicMock()
    actor_id = ActorId("test_actor")
    kernel = MagicMock()
    return StepActor(ctx, actor_id, kernel)


async def test_initialize_step(actor_context):
    input_data = json.dumps({
        "step_info": {
            "state": {"name": "TestStep", "id": "step_1"},
            "inner_step_python_type": "SomeStepType",
            "edges": {},
        },
        "parent_process_id": "parent_1",
    })

    with (
        patch.object(actor_context._state_manager, "try_add_state", new=AsyncMock()) as mock_try_add_state,
        patch.object(actor_context._state_manager, "save_state", new=AsyncMock()) as mock_save_state,
    ):
        await actor_context.initialize_step(input_data)

        assert actor_context.step_info is not None
        mock_try_add_state.assert_any_call("DaprStepInfo", actor_context.step_info)
        mock_save_state.assert_called_once()


async def test_prepare_incoming_messages(actor_context):
    message = ProcessMessage(
        source_id="source_1",
        destination_id="dest_1",
        function_name="test_function",
        values={"param1": "value1"},
    )
    mock_message_json = json.dumps(message.model_dump())

    expected_state_key = "incomingMessagesState"

    with (
        patch("dapr.actor.ActorProxy.create", new=MagicMock()) as mock_actor_proxy,
        patch.object(actor_context._state_manager, "try_add_state", new=AsyncMock()) as mock_try_add_state,
        patch.object(actor_context._state_manager, "save_state", new=AsyncMock()) as mock_save_state,
    ):
        mock_queue = AsyncMock()
        mock_queue.dequeue_all.return_value = [mock_message_json]
        mock_actor_proxy.return_value = mock_queue

        incoming_message_count = await actor_context.prepare_incoming_messages()

        assert incoming_message_count == 1
        assert actor_context.incoming_messages.qsize() == 1
        mock_try_add_state.assert_called_with(expected_state_key, [mock_message_json])
        mock_save_state.assert_called_once()


async def test_process_incoming_messages(actor_context):
    actor_context.step_info = DaprStepInfo(
        state=KernelProcessStepState(name="Test Step", id="step_123"),
        inner_step_python_type="SomeStepType",
        edges={},
    )

    message = ProcessMessage(
        source_id="source_1",
        destination_id="dest_1",
        function_name="test_function",
        values={"param1": "value1"},
    )
    actor_context.incoming_messages.put(message)

    with (
        patch.object(actor_context, "handle_message", new=AsyncMock()) as mock_handle_message,
        patch.object(actor_context._state_manager, "save_state", new=AsyncMock()) as mock_save_state,
        patch.object(
            actor_context._state_manager, "try_add_state", new=AsyncMock(return_value=True)
        ) as mock_try_add_state,
    ):
        await actor_context.process_incoming_messages()
        mock_handle_message.assert_called_once_with(message)
        mock_save_state.assert_called_once()
        expected_messages = []
        expected_messages = [json.dumps(msg.model_dump()) for msg in list(actor_context.incoming_messages.queue)]
        mock_try_add_state.assert_any_call("incomingMessagesState", expected_messages)
