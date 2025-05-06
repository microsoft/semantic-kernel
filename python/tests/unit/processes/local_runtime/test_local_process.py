# Copyright (c) Microsoft. All rights reserved.


import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from semantic_kernel.exceptions.kernel_exceptions import KernelException
from semantic_kernel.exceptions.process_exceptions import ProcessEventUndefinedException
from semantic_kernel.kernel import Kernel
from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess
from semantic_kernel.processes.kernel_process.kernel_process_edge import KernelProcessEdge
from semantic_kernel.processes.kernel_process.kernel_process_event import (
    KernelProcessEvent,
    KernelProcessEventVisibility,
)
from semantic_kernel.processes.kernel_process.kernel_process_state import KernelProcessState
from semantic_kernel.processes.kernel_process.kernel_process_step_info import KernelProcessStepInfo
from semantic_kernel.processes.local_runtime.local_message import LocalMessage
from semantic_kernel.processes.local_runtime.local_process import LocalProcess
from semantic_kernel.processes.local_runtime.local_step import LocalStep


@pytest.fixture
def mock_kernel():
    return MagicMock(spec=Kernel)


@pytest.fixture
def mock_process_with_output_edges(mock_process, mock_kernel, build_model):
    """Fixture to create a LocalProcess with predefined output edges."""
    local_process = LocalProcess(process=mock_process, kernel=mock_kernel)
    local_process.output_edges = {"valid_event_id": MagicMock()}
    return local_process


@pytest.fixture
def mock_process(mock_kernel):
    state = MagicMock(spec=KernelProcessState)
    state.name = "test_process"
    state.id = "process_001"
    step_info = MagicMock(spec=KernelProcessStepInfo)
    step_info.state = state
    process = MagicMock(spec=KernelProcess)
    process.state = state
    process.steps = [step_info]
    process.edges = {"event_001": [MagicMock(spec=KernelProcessEdge)]}
    return process


@pytest.fixture
def mock_local_step():
    step_info = MagicMock(spec=KernelProcessStepInfo)
    step_info.state.name = "step_name"
    step_info.state.id = "step_001"
    local_step = MagicMock(spec=LocalProcess)
    local_step.step_info = step_info
    local_step.id = "step_001"
    return local_step


@pytest.fixture
def build_model():
    from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess  # noqa: F401

    LocalProcess.model_rebuild()


def test_initialization(mock_process, mock_kernel, build_model):
    # Act
    local_process = LocalProcess(process=mock_process, kernel=mock_kernel)

    # Assert
    assert local_process.process == mock_process
    assert local_process.kernel == mock_kernel
    assert not local_process.initialize_task
    assert len(local_process.step_infos) == len(mock_process.steps)
    assert local_process.step_infos[0] == mock_process.steps[0]
    assert local_process.external_event_queue.empty()


def test_initialization_max_supersteps(mock_process, mock_kernel, build_model):
    # Act
    local_process = LocalProcess(process=mock_process, kernel=mock_kernel, max_supersteps=10)

    # Assert
    assert local_process.process == mock_process
    assert local_process.kernel == mock_kernel
    assert not local_process.initialize_task
    assert len(local_process.step_infos) == len(mock_process.steps)
    assert local_process.step_infos[0] == mock_process.steps[0]
    assert local_process.external_event_queue.empty()
    assert local_process.max_supersteps == 10


def test_ensure_initialized(mock_process, mock_kernel, build_model):
    # Arrange
    local_process = LocalProcess(process=mock_process, kernel=mock_kernel)

    with patch.object(
        LocalProcess, "initialize_process", wraps=local_process.initialize_process
    ) as mock_initialize_process:
        # Act
        local_process.ensure_initialized()

        # Assert
        mock_initialize_process.assert_called_once()
        assert local_process.initialize_task is True


def test_ensure_initialized_already_done(mock_process, mock_kernel, build_model):
    # Arrange
    local_process = LocalProcess(process=mock_process, kernel=mock_kernel)
    local_process.initialize_task = True  # Simulate that the process is already initialized

    with patch.object(
        LocalProcess, "initialize_process", wraps=local_process.initialize_process
    ) as mock_initialize_process:
        # Act
        local_process.ensure_initialized()

        # Assert
        mock_initialize_process.assert_not_called()


async def test_start(mock_process, mock_kernel, build_model):
    # Arrange
    local_process = LocalProcess(process=mock_process, kernel=mock_kernel)

    # Patch `ensure_initialized` to track its call but still run the original method.
    with (
        patch.object(
            LocalProcess, "ensure_initialized", wraps=local_process.ensure_initialized
        ) as mock_ensure_initialized,
        patch.object(LocalProcess, "internal_execute", new_callable=AsyncMock),
    ):
        # Act
        await local_process.start(keep_alive=True)

        # Assert
        mock_ensure_initialized.assert_called_once()
        assert local_process.process_task is not None
        assert isinstance(local_process.process_task, asyncio.Task)


async def test_run_once(mock_process, mock_kernel, build_model):
    # Arrange
    local_process = LocalProcess(process=mock_process, kernel=mock_kernel)
    local_process.process_task = AsyncMock(spec=asyncio.Task)

    # Patch `ensure_initialized` to track its call but still run the original method.
    with (
        patch.object(LocalProcess, "ensure_initialized", wraps=local_process.ensure_initialized),
        patch.object(LocalProcess, "start", new_callable=AsyncMock),
    ):
        # Act
        await local_process.start(keep_alive=True)

        # Assert
        assert local_process.process_task is not None
        assert isinstance(local_process.process_task, asyncio.Task)


async def test_stop_running_task(mock_process, mock_kernel, build_model):
    # Arrange
    local_process = LocalProcess(process=mock_process, kernel=mock_kernel)
    local_process.process_task = asyncio.create_task(asyncio.sleep(1))  # Mock a running task

    # Act
    await local_process.stop()

    # Assert
    assert local_process.process_task.cancelled()


async def test_stop_no_running_task(mock_process, mock_kernel, build_model):
    # Arrange
    local_process = LocalProcess(process=mock_process, kernel=mock_kernel)
    local_process.process_task = None

    # Act
    await local_process.stop()

    # Assert
    assert local_process.process_task is None  # No action should be taken


async def test_send_message(mock_process, mock_kernel, build_model):
    # Arrange
    local_process = LocalProcess(process=mock_process, kernel=mock_kernel)
    process_event = MagicMock(spec=KernelProcessEvent)

    # Act
    await local_process.send_message(process_event)

    # Assert
    assert not local_process.external_event_queue.empty()
    assert local_process.external_event_queue.get() == process_event


async def test_send_message_with_invalid_event(mock_process, mock_kernel, build_model):
    # Arrange
    local_process = LocalProcess(process=mock_process, kernel=mock_kernel)

    # Act & Assert
    with pytest.raises(ProcessEventUndefinedException):
        await local_process.send_message(None)


async def test_run_once_with_valid_event(mock_process, mock_kernel, build_model):
    # Arrange
    local_process = LocalProcess(process=mock_process, kernel=mock_kernel)
    process_event = MagicMock(spec=KernelProcessEvent)

    async def mock_coroutine():
        return None

    task = asyncio.create_task(mock_coroutine())
    local_process.process_task = task

    with patch.object(LocalProcess, "start", new_callable=AsyncMock) as mock_start:
        # Act
        await local_process.run_once(process_event)

        # Assert
        assert not local_process.external_event_queue.empty()
        assert local_process.external_event_queue.get() == process_event
        mock_start.assert_awaited_once_with(keep_alive=False)
        assert local_process.process_task.done()


async def test_run_once_with_no_event_raises_exception(mock_process, mock_kernel, build_model):
    # Arrange
    local_process = LocalProcess(process=mock_process, kernel=mock_kernel)

    # Act & Assert
    with pytest.raises(ProcessEventUndefinedException):
        await local_process.run_once(None)


async def test_run_once_without_process_task(mock_process, mock_kernel, build_model):
    # Arrange
    local_process = LocalProcess(process=mock_process, kernel=mock_kernel)
    process_event = MagicMock(spec=KernelProcessEvent)
    local_process.process_task = None  # Simulate no process task

    with patch.object(LocalProcess, "start", new_callable=AsyncMock) as mock_start:
        # Act
        await local_process.run_once(process_event)

        # Assert
        assert not local_process.external_event_queue.empty()
        assert local_process.external_event_queue.get() == process_event
        mock_start.assert_awaited_once_with(keep_alive=False)
        assert local_process.process_task is None


def test_initialize_process(mock_process, mock_kernel, build_model):
    # Arrange
    local_process = LocalProcess(process=mock_process, kernel=mock_kernel)

    with (
        patch(
            "semantic_kernel.processes.local_runtime.local_process.LocalProcess.__init__", return_value=None
        ) as mock_local_process_init,
        patch(
            "semantic_kernel.processes.local_runtime.local_step.LocalStep.__init__", return_value=None
        ) as mock_local_step_init,
    ):
        # Act
        local_process.initialize_process()

        # Assert
        assert local_process.output_edges == {"event_001": list(mock_process.edges["event_001"])}

        for step_info in mock_process.steps:
            if isinstance(step_info, KernelProcess):
                mock_local_process_init.assert_called_with(
                    process=step_info,
                    kernel=mock_kernel,
                    parent_process_id=local_process.id,
                )
            else:
                mock_local_step_init.assert_called_with(
                    step_info=step_info,
                    kernel=mock_kernel,
                    factories={},
                    parent_process_id=local_process.id,
                )

        assert len(local_process.steps) == len(mock_process.steps)


async def test_handle_message_without_target_event_id(mock_process_with_output_edges, build_model):
    # Arrange
    local_process = mock_process_with_output_edges
    message = MagicMock(spec=LocalMessage)
    message.target_event_id = None  # Simulate missing target_event_id

    # Act & Assert
    with pytest.raises(KernelException) as exc_info:
        await local_process.handle_message(message)

    # Verify that the exception message is correct
    assert "The target event id must be specified" in str(exc_info.value)


async def test_handle_message_with_valid_event_id(mock_process_with_output_edges, build_model):
    # Arrange
    local_process = mock_process_with_output_edges
    message = MagicMock(spec=LocalMessage)
    message.target_event_id = "valid_event_id"
    message.target_event_data = {"key": "value"}  # Simulate message data

    # Patch the run_once method on the LocalProcess class to prevent actual execution and track the call.
    with patch.object(LocalProcess, "run_once", new_callable=AsyncMock) as mock_run_once:
        # Act
        await local_process.handle_message(message)

        # Assert
        # Verify that run_once was called with the correct KernelProcessEvent
        mock_run_once.assert_awaited_once()
        event = mock_run_once.call_args[0][0]
        assert isinstance(event, KernelProcessEvent)
        assert event.id == "valid_event_id"
        assert event.data == message.target_event_data
        assert event.visibility == KernelProcessEventVisibility.Internal


END_PROCESS_ID = "END"


@pytest.fixture
def mock_process_with_steps(mock_process, mock_kernel, build_model):
    """Fixture to create a LocalProcess with mock steps."""
    local_process = LocalProcess(process=mock_process, kernel=mock_kernel)

    # Create real LocalStep instances
    state_1 = MagicMock(spec=KernelProcessState)
    state_1.name = "step_1_state"
    state_1.id = "step_1_id"

    step_info_1 = MagicMock(spec=KernelProcessStepInfo)
    step_info_1.state = state_1

    state_2 = MagicMock(spec=KernelProcessState)
    state_2.name = "step_2_state"
    state_2.id = "step_2_id"

    step_info_2 = MagicMock(spec=KernelProcessStepInfo)
    step_info_2.state = state_2

    step_1 = LocalStep(step_info=step_info_1, kernel=mock_kernel, parent_process_id="test_process")
    step_2 = LocalStep(step_info=step_info_2, kernel=mock_kernel, parent_process_id="test_process")

    local_process.steps = [step_1, step_2]
    return local_process
