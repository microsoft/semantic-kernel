# Copyright (c) Microsoft. All rights reserved.


import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from semantic_kernel.exceptions.process_exceptions import ProcessEventUndefinedException
from semantic_kernel.kernel import Kernel
from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess
from semantic_kernel.processes.kernel_process.kernel_process_edge import KernelProcessEdge
from semantic_kernel.processes.kernel_process.kernel_process_event import (
    KernelProcessEvent,
)
from semantic_kernel.processes.kernel_process.kernel_process_state import KernelProcessState
from semantic_kernel.processes.kernel_process.kernel_process_step_info import KernelProcessStepInfo
from semantic_kernel.processes.local_runtime.local_process import LocalProcess


@pytest.fixture
def mock_kernel():
    return MagicMock(spec=Kernel)


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


@pytest.mark.asyncio
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


@pytest.mark.asyncio
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


@pytest.mark.asyncio
async def test_stop_running_task(mock_process, mock_kernel, build_model):
    # Arrange
    local_process = LocalProcess(process=mock_process, kernel=mock_kernel)
    local_process.process_task = asyncio.create_task(asyncio.sleep(1))  # Mock a running task

    # Act
    await local_process.stop()

    # Assert
    assert local_process.process_task.cancelled()


@pytest.mark.asyncio
async def test_stop_no_running_task(mock_process, mock_kernel, build_model):
    # Arrange
    local_process = LocalProcess(process=mock_process, kernel=mock_kernel)
    local_process.process_task = None

    # Act
    await local_process.stop()

    # Assert
    assert local_process.process_task is None  # No action should be taken


@pytest.mark.asyncio
async def test_send_message(mock_process, mock_kernel, build_model):
    # Arrange
    local_process = LocalProcess(process=mock_process, kernel=mock_kernel)
    process_event = MagicMock(spec=KernelProcessEvent)

    # Act
    await local_process.send_message(process_event)

    # Assert
    assert not local_process.external_event_queue.empty()
    assert local_process.external_event_queue.get() == process_event


@pytest.mark.asyncio
async def test_send_message_with_invalid_event(mock_process, mock_kernel, build_model):
    # Arrange
    local_process = LocalProcess(process=mock_process, kernel=mock_kernel)

    # Act & Assert
    with pytest.raises(ProcessEventUndefinedException):
        await local_process.send_message(None)
