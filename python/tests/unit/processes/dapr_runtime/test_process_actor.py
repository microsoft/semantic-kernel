# Copyright (c) Microsoft. All rights reserved.

import asyncio
import json
from queue import Queue
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dapr.actor.id import ActorId
from dapr.actor.runtime._type_information import ActorTypeInformation
from dapr.actor.runtime.context import ActorRuntimeContext

from semantic_kernel.exceptions.kernel_exceptions import KernelException
from semantic_kernel.exceptions.process_exceptions import ProcessEventUndefinedException
from semantic_kernel.processes.dapr_runtime.actors.actor_state_key import ActorStateKeys
from semantic_kernel.processes.dapr_runtime.actors.process_actor import ProcessActor
from semantic_kernel.processes.dapr_runtime.dapr_process_info import DaprProcessInfo
from semantic_kernel.processes.dapr_runtime.dapr_step_info import DaprStepInfo
from semantic_kernel.processes.kernel_process.kernel_process_event import KernelProcessEvent
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


@pytest.fixture
def actor() -> ProcessActor:
    """Create a fresh ProcessActor with mocked dependencies."""
    # Arrange: Create a dummy runtime context and ProcessActor instance
    actor_id = ActorId("test_actor")
    runtime_context = MagicMock()
    kernel = MagicMock()
    actor_obj = ProcessActor(runtime_context, actor_id, kernel=kernel, factories={})
    # Mock internal state manager
    actor_obj._state_manager = AsyncMock()
    actor_obj._state_manager.try_get_state = AsyncMock(return_value=(False, None))
    actor_obj._state_manager.try_add_state = AsyncMock()
    actor_obj._state_manager.save_state = AsyncMock()
    return actor_obj


def test_name_uninitialized(actor: ProcessActor):
    """Test that accessing name before initialization raises KernelException."""
    with pytest.raises(KernelException) as exc_info:
        _ = actor.name
    assert "must be initialized before accessing the name" in str(exc_info.value)


@pytest.mark.asyncio
async def test_start_not_initialized(actor: ProcessActor):
    """Test that start() without initialization raises ValueError."""
    actor.initialize_task = False
    with pytest.raises(ValueError):
        await actor.start()


@pytest.mark.asyncio
async def test_run_once_none_event(actor: ProcessActor):
    """Test that run_once(None) raises ProcessEventUndefinedException."""
    actor.initialize_task = True
    with pytest.raises(ProcessEventUndefinedException):
        await actor.run_once(None)  # type: ignore


@pytest.mark.asyncio
async def test_send_message_none_event(actor: ProcessActor):
    """Test that send_message(None) raises ProcessEventUndefinedException."""
    with pytest.raises(ProcessEventUndefinedException):
        await actor.send_message(None)  # type: ignore


def test_send_message_success(actor: ProcessActor):
    """Test that send_message enqueues the event into external_event_queue."""
    event = KernelProcessEvent(id="e1", data="d1")
    asyncio.run(actor.send_message(event))
    assert isinstance(actor.external_event_queue, Queue)
    assert not actor.external_event_queue.empty()
    queued = actor.external_event_queue.get()
    assert queued is event


@pytest.mark.asyncio
async def test_to_dapr_process_info_uninitialized(actor: ProcessActor):
    """Test to_dapr_process_info raises ValueError if process is None."""
    actor.process = None
    with pytest.raises(ValueError) as exc:
        await actor.to_dapr_process_info()
    assert "must be initialized before converting" in str(exc.value)


@pytest.mark.asyncio
async def test_to_dapr_process_info_inner_step_type_none(actor: ProcessActor):
    """Test to_dapr_process_info raises ValueError if inner_step_python_type is None."""
    actor.process = MagicMock()
    # Simulate a process with missing inner_step_python_type
    actor.process.inner_step_python_type = None
    actor.process.state = MagicMock(name="Proc", id="pid")
    actor.steps = []
    with pytest.raises(ValueError) as exc:
        await actor.to_dapr_process_info()
    assert "inner step type must be defined" in str(exc.value)


@pytest.mark.asyncio
async def test_to_dapr_process_info_success(actor: ProcessActor):
    """Test to_dapr_process_info returns correct dict for initialized process with no steps."""
    proc_state = KernelProcessState(name="Proc", version="1.0", id="test_actor")
    dapr_proc = DaprProcessInfo(
        inner_step_python_type="Type1",
        state=proc_state,
        edges={},
        steps=[],
    )
    actor.process = dapr_proc
    actor.steps = []
    result = await actor.to_dapr_process_info()
    assert result == dapr_proc.model_dump()


@pytest.mark.asyncio
async def test_stop_no_task(actor: ProcessActor):
    """Test stop() returns normally when no process_task is running."""
    actor.process_task = None
    await actor.stop()


def test_name_after_manual_set(actor: ProcessActor):
    """Test that name property returns the correct name after manual initialization."""
    actor.process = MagicMock()
    actor.process.state = MagicMock()
    actor.process.state.name = "MyProcess"
    actor.process.state.id = "id123"
    assert actor.name == "MyProcess"


@pytest.mark.asyncio
async def test_send_outgoing_public_events_no_parent(actor: ProcessActor):
    """Test send_outgoing_public_events does nothing if parent_process_id is None."""
    actor.parent_process_id = None
    with patch("semantic_kernel.processes.dapr_runtime.actors.process_actor.ActorProxy.create") as mock_proxy:
        await actor.send_outgoing_public_events()
        mock_proxy.assert_not_called()
