# Copyright (c) Microsoft. All rights reserved.

import pytest
from pydantic import ValidationError

from semantic_kernel.processes.kernel_process.kernel_process_function_target import KernelProcessFunctionTarget


def test_initialization():
    # Arrange
    step_id = "step_001"
    function_name = "execute_task"
    parameter_name = "input_data"
    target_event_id = "event_001"

    # Act
    target = KernelProcessFunctionTarget(
        step_id=step_id, function_name=function_name, parameter_name=parameter_name, target_event_id=target_event_id
    )

    # Assert
    assert target.step_id == step_id
    assert target.function_name == function_name
    assert target.parameter_name == parameter_name
    assert target.target_event_id == target_event_id


def test_initialization_with_defaults():
    # Arrange
    step_id = "step_002"
    function_name = "process_data"

    # Act
    target = KernelProcessFunctionTarget(step_id=step_id, function_name=function_name)

    # Assert
    assert target.step_id == step_id
    assert target.function_name == function_name
    assert target.parameter_name is None
    assert target.target_event_id is None


def test_invalid_initialization():
    # Arrange
    step_id = 12345  # Invalid type
    function_name = "compute"

    # Act & Assert
    with pytest.raises(ValidationError):
        KernelProcessFunctionTarget(step_id=step_id, function_name=function_name)


def test_partial_initialization_with_parameter_name():
    # Arrange
    step_id = "step_003"
    function_name = "calculate"
    parameter_name = "value"

    # Act
    target = KernelProcessFunctionTarget(step_id=step_id, function_name=function_name, parameter_name=parameter_name)

    # Assert
    assert target.step_id == step_id
    assert target.function_name == function_name
    assert target.parameter_name == parameter_name
    assert target.target_event_id is None
