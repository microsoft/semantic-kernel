# Copyright (c) Microsoft. All rights reserved.

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dapr.actor.id import ActorId
from dapr.actor.runtime._type_information import ActorTypeInformation
from dapr.actor.runtime.context import ActorRuntimeContext

from semantic_kernel.processes.dapr_runtime.actors.actor_state_key import ActorStateKeys
from semantic_kernel.processes.dapr_runtime.actors.process_actor import ProcessActor
from semantic_kernel.processes.dapr_runtime.dapr_process_info import DaprProcessInfo
from semantic_kernel.processes.dapr_runtime.dapr_step_info import DaprStepInfo
from semantic_kernel.processes.kernel_process.kernel_process_state import KernelProcessState


@pytest.fixture
def actor_context():
    actor_id = ActorId("test_actor")
    actor_type_info = ActorTypeInformation.create(ProcessActor)
    runtime_context = ActorRuntimeContext(
        actor_type_info=actor_type_info,
        message_serializer=MagicMock(),
        state_serializer=MagicMock(),
        actor_client=MagicMock(),
    )
    kernel_mock = MagicMock()
    actor = ProcessActor(runtime_context, actor_id, kernel=kernel_mock, factories={})

    actor._state_manager = AsyncMock()
    actor._state_manager.try_add_state = AsyncMock(return_value=True)
    actor._state_manager.try_get_state = AsyncMock(return_value=(True, {}))
    actor._state_manager.save_state = AsyncMock()

    asyncio.run(actor._on_activate())
    return actor


def clean_structure(data):
    """Recursively remove null values and empty dictionaries for direct comparison."""
    if isinstance(data, dict):
        return {k: clean_structure(v) for k, v in data.items() if v not in [None, {}]}
    if isinstance(data, list):
        return [clean_structure(item) for item in data]
    return data


async def test_initialize_process(actor_context):
    input_data = {
        "process_info": {
            "type": "DaprProcessInfo",
            "state": {"type": "KernelProcessState", "name": "Test Process", "version": "1.0", "id": "proc_123"},
            "steps": [
                {
                    "type": "DaprStepInfo",
                    "inner_step_python_type": "SomeStepType",
                    "state": {"type": "KernelProcessState", "name": "Step1", "version": "1.0", "id": "step_123"},
                }
            ],
            "inner_step_python_type": "SomeProcessType",
            "edges": {},
        },
        "parent_process_id": "parent_123",
    }

    expected_process_info = clean_structure(input_data["process_info"])

    dapr_process_info_instance = DaprProcessInfo(
        inner_step_python_type="SomeProcessType",
        state=KernelProcessState(name="Test Process", version="1.0", id="proc_123"),
        edges={},
        steps=[
            DaprStepInfo(
                inner_step_python_type="SomeStepType",
                state=KernelProcessState(name="Step1", version="1.0", id="step_123"),
                edges={},
            )
        ],
    )

    with (
        patch.multiple(
            actor_context,
            _initialize_process_actor=AsyncMock(),
            _state_manager=actor_context._state_manager,
        ),
        patch.object(actor_context._state_manager, "save_state", new=AsyncMock()) as mock_save_state,
    ):
        await actor_context.initialize_process(input_data)

        actual_calls = actor_context._state_manager.try_add_state.call_args_list
        actual_process_info_call = next(
            (call for call in actual_calls if call[0][0] == ActorStateKeys.ProcessInfoState.value), None
        )

        assert actual_process_info_call is not None, "ProcessInfoState call was not found."
        actual_process_info = clean_structure(actual_process_info_call[0][1])

        assert actual_process_info == expected_process_info, (
            f"Expected: {json.dumps(expected_process_info)}, but got: {json.dumps(actual_process_info)}"
        )

        mock_save_state.assert_called_once()

        actor_context._initialize_process_actor.assert_called_once_with(dapr_process_info_instance, "parent_123")


async def test_start_process(actor_context):
    actor_context.initialize_task = True

    with patch.object(actor_context, "internal_execute", new=AsyncMock()) as mock_internal_execute:
        await actor_context.start(keep_alive=False)

        assert actor_context.process_task is not None
        mock_internal_execute.assert_called_once()
        assert not actor_context.process_task.done()


def test_run_once(actor_context):
    actor_context.initialize_task = True
    process_event = '{"event": "test_event"}'

    with patch(
        "semantic_kernel.processes.dapr_runtime.actors.process_actor.ActorProxy.create", return_value=AsyncMock()
    ) as mock_proxy:
        asyncio.run(actor_context.run_once(process_event))

        external_event_queue = mock_proxy.return_value
        external_event_queue.enqueue.assert_called_once_with(process_event)

        assert actor_context.process_task is not None


async def test_stop(actor_context):
    actor_context.initialize_task = True
    actor_context.process_task = asyncio.create_task(asyncio.sleep(1))

    await actor_context.stop()

    assert actor_context.process_task.done()


def test_get_process_info(actor_context):
    with patch.object(actor_context, "to_dapr_process_info", return_value=MagicMock()) as mock_to_dapr_process_info:
        process_info = asyncio.run(actor_context.get_process_info())
        mock_to_dapr_process_info.assert_called_once()
        assert process_info is mock_to_dapr_process_info.return_value


def test_handle_message(actor_context):
    message_mock = MagicMock()
    message_mock.target_event_id = "test_event"
    actor_context.output_edges = {"test_event": [MagicMock()]}

    with patch.object(actor_context, "run_once", new=AsyncMock()) as mock_run_once:
        asyncio.run(actor_context.handle_message(message_mock))

        mock_run_once.assert_called_once()
