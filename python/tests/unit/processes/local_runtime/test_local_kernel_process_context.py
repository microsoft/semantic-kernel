# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from semantic_kernel.kernel import Kernel
from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess
from semantic_kernel.processes.kernel_process.kernel_process_state import KernelProcessState
from semantic_kernel.processes.kernel_process.kernel_process_step_info import KernelProcessStepInfo
from semantic_kernel.processes.local_runtime.local_event import KernelProcessEvent
from semantic_kernel.processes.local_runtime.local_kernel_process_context import LocalKernelProcessContext
from semantic_kernel.processes.local_runtime.local_process import LocalProcess


@pytest.fixture
def mock_kernel():
    return MagicMock(spec=Kernel)


@pytest.fixture
def mock_process():
    state = MagicMock(spec=KernelProcessState)
    state.name = "test_process"
    step_info = MagicMock(spec=KernelProcessStepInfo)
    process = MagicMock(spec=KernelProcess)
    process.state = state
    process.steps = [step_info]
    process.factories = {}
    return process


async def test_initialization(mock_process, mock_kernel):
    # Arrange
    mock_process.state.id = "test_id"

    # Act
    context = LocalKernelProcessContext(process=mock_process, kernel=mock_kernel)

    # Assert
    assert context.local_process is not None


async def test_initialization_with_missing_kernel_throws(mock_process):
    # Arrange
    mock_process.state.id = "test_id"

    # Act & Assert
    with pytest.raises(ValueError, match="Kernel must be provided"):
        _ = LocalKernelProcessContext(process=mock_process, kernel=None)


def test_initialization_raises_value_error_for_missing_process_state(mock_kernel):
    # Arrange
    mock_process = MagicMock(spec=KernelProcess)
    mock_process.state = None

    # Act & Assert
    with pytest.raises(ValueError, match="Process and process state must be provided and have a valid name"):
        LocalKernelProcessContext(process=mock_process, kernel=mock_kernel)


async def test_start_with_event(mock_process, mock_kernel):
    # Arrange
    mock_process.state.id = "test_id"
    context = LocalKernelProcessContext(process=mock_process, kernel=mock_kernel)
    event = MagicMock(spec=KernelProcessEvent)

    # Patch the 'run_once' method of LocalProcess.
    with patch.object(LocalProcess, "run_once", new=AsyncMock()) as mock_run_once:
        # Act
        await context.start_with_event(initial_event=event)

        # Assert
        mock_run_once.assert_awaited_once_with(event)


async def test_send_event(mock_process, mock_kernel):
    # Arrange
    mock_process.state.id = "test_id"
    context = LocalKernelProcessContext(process=mock_process, kernel=mock_kernel)
    event = MagicMock(spec=KernelProcessEvent)

    # Patch the 'send_message' method of LocalProcess.
    with patch.object(LocalProcess, "send_message", new=AsyncMock()) as mock_send_message:
        # Act
        await context.send_event(event)

        # Assert
        mock_send_message.assert_awaited_once_with(event)


async def test_stop(mock_process, mock_kernel):
    # Arrange
    mock_process.state.id = "test_id"
    context = LocalKernelProcessContext(process=mock_process, kernel=mock_kernel)

    # Patch the 'stop' method of LocalProcess.
    with patch.object(LocalProcess, "stop", new=AsyncMock()) as mock_stop:
        # Act
        await context.stop()

        # Assert
        mock_stop.assert_awaited_once()


async def test_get_state(mock_process, mock_kernel):
    # Arrange
    mock_process.state.id = "test_id"
    context = LocalKernelProcessContext(process=mock_process, kernel=mock_kernel)

    # Patch the 'get_process_info' method of LocalProcess.
    with patch.object(
        LocalProcess, "get_process_info", new=AsyncMock(return_value=mock_process)
    ) as mock_get_process_info:
        # Act
        result = await context.get_state()

        # Assert
        assert result == mock_process
        mock_get_process_info.assert_awaited_once()


async def test_async_context_manager(mock_process, mock_kernel):
    # Arrange
    mock_process.state.id = "test_id"
    context = LocalKernelProcessContext(process=mock_process, kernel=mock_kernel)

    # Patch the 'dispose' method of the LocalKernelProcessContext class itself.
    with patch.object(LocalKernelProcessContext, "dispose", new=AsyncMock()) as mock_dispose:
        # Act
        async with context as ctx:
            assert ctx == context

        # Assert
        mock_dispose.assert_awaited_once()
