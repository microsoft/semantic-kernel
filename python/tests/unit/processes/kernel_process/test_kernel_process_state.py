# Copyright (c) Microsoft. All rights reserved.

import pytest
from pydantic import ValidationError

from semantic_kernel.processes.kernel_process.kernel_process_state import KernelProcessState


def test_initialization_with_name_and_id():
    # Arrange
    name = "test_process"
    process_id = "1234"

    # Act
    state = KernelProcessState(name=name, id=process_id)

    # Assert
    assert state.name == name
    assert state.id == process_id
    assert state.state is None


def test_initialization_with_name_only():
    # Arrange
    name = "test_process_without_id"

    # Act
    state = KernelProcessState(name=name)

    # Assert
    assert state.name == name
    assert state.id is None
    assert state.state is None


def test_setting_state_value():
    # Arrange
    name = "test_process"
    state_value = {"key": "value"}

    # Act
    state = KernelProcessState(name=name)
    state.state = state_value

    # Assert
    assert state.state == state_value


def test_initialization_with_invalid_name():
    # Arrange
    name = 12345  # Invalid type for name

    # Act & Assert
    with pytest.raises(ValidationError):
        KernelProcessState(name=name)
