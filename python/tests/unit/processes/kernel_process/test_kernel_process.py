# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess
from semantic_kernel.processes.kernel_process.kernel_process_edge import KernelProcessEdge
from semantic_kernel.processes.kernel_process.kernel_process_event import KernelProcessEvent
from semantic_kernel.processes.kernel_process.kernel_process_state import KernelProcessState
from semantic_kernel.processes.kernel_process.kernel_process_step_info import KernelProcessStepInfo


def test_initialization_with_valid_parameters():
    # Arrange
    state = MagicMock(spec=KernelProcessState)
    state.name = "valid_state"
    steps = [MagicMock(spec=KernelProcessStepInfo)]
    edges = {"step1": [MagicMock(spec=KernelProcessEdge)]}

    # Act
    process = KernelProcess(state=state, steps=steps, edges=edges)

    # Assert
    assert process.state == state
    assert process.steps == steps
    assert process.output_edges == edges


def test_initialization_with_no_steps():
    # Arrange
    state = MagicMock(spec=KernelProcessState)
    state.name = "state_without_steps"

    # Act & Assert
    with pytest.raises(ValueError, match="steps cannot be None"):
        KernelProcess(state=state, steps=[])


def test_initialization_with_no_state():
    # Arrange
    steps = [MagicMock(spec=KernelProcessStepInfo)]
    edges = {"step1": [MagicMock(spec=KernelProcessEdge)]}

    # Act & Assert
    with pytest.raises(ValueError, match="state cannot be None"):
        KernelProcess(state=None, steps=steps, edges=edges)


def test_initialization_with_no_state_name():
    # Arrange
    state = MagicMock(spec=KernelProcessState)
    state.name = None  # Invalid state name
    steps = [MagicMock(spec=KernelProcessStepInfo)]

    # Act & Assert
    with pytest.raises(ValueError, match="state.Name cannot be None"):
        KernelProcess(state=state, steps=steps)


@pytest.mark.asyncio
async def test_start_method():
    # Arrange
    state = MagicMock(spec=KernelProcessState)
    state.name = "startable_state"
    steps = [MagicMock(spec=KernelProcessStepInfo)]
    process = KernelProcess(state=state, steps=steps)
    kernel = MagicMock()
    initial_event = MagicMock(spec=KernelProcessEvent)

    with patch(
        "semantic_kernel.processes.kernel_process.kernel_process.LocalKernelProcessContext",
        autospec=True,
    ) as MockContext:
        mock_context_instance = MockContext.return_value
        mock_context_instance.__aenter__.return_value = mock_context_instance
        mock_context_instance.__aexit__ = AsyncMock()
        mock_context_instance.start_with_event = AsyncMock()

        # Act
        result = await process.start(kernel=kernel, initial_event=initial_event)

        # Assert
        mock_context_instance.start_with_event.assert_awaited_once_with(initial_event)
        assert result == mock_context_instance
