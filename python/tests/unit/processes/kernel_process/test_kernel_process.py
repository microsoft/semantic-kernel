# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import MagicMock

import pytest

from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess
from semantic_kernel.processes.kernel_process.kernel_process_edge import KernelProcessEdge
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
