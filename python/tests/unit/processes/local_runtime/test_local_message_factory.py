# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import MagicMock

import pytest

from semantic_kernel.processes.kernel_process.kernel_process_edge import KernelProcessEdge
from semantic_kernel.processes.kernel_process.kernel_process_function_target import KernelProcessFunctionTarget
from semantic_kernel.processes.local_runtime.local_message import LocalMessage
from semantic_kernel.processes.local_runtime.local_message_factory import LocalMessageFactory


def test_create_from_edge_with_data():
    # Arrange
    edge = MagicMock(spec=KernelProcessEdge)
    edge.source_step_id = "source_001"
    edge.output_target = KernelProcessFunctionTarget(
        step_id="target_001", function_name="process_data", parameter_name="input_data", target_event_id="event_123"
    )
    data = {"key": "value"}

    # Act
    message = LocalMessageFactory.create_from_edge(edge=edge, data=data)

    # Assert
    assert isinstance(message, LocalMessage)
    assert message.source_id == "source_001"
    assert message.destination_id == "target_001"
    assert message.function_name == "process_data"
    assert message.values == {"input_data": data}
    assert message.target_event_id == "event_123"
    assert message.target_event_data == data


def test_create_from_edge_without_parameter_name():
    # Arrange
    edge = MagicMock(spec=KernelProcessEdge)
    edge.source_step_id = "source_002"
    edge.output_target = KernelProcessFunctionTarget(
        step_id="target_002", function_name="execute_task", parameter_name=None, target_event_id="event_456"
    )
    data = {"another_key": "another_value"}

    # Act
    message = LocalMessageFactory.create_from_edge(edge=edge, data=data)

    # Assert
    assert isinstance(message, LocalMessage)
    assert message.source_id == "source_002"
    assert message.destination_id == "target_002"
    assert message.function_name == "execute_task"
    assert message.values == {}  # No parameter name, so values should be empty
    assert message.target_event_id == "event_456"
    assert message.target_event_data == data


def test_create_from_edge_with_no_data():
    # Arrange
    edge = MagicMock(spec=KernelProcessEdge)
    edge.source_step_id = "source_003"
    edge.output_target = KernelProcessFunctionTarget(
        step_id="target_003", function_name="perform_action", parameter_name="param_name", target_event_id="event_789"
    )
    data = None

    # Act
    message = LocalMessageFactory.create_from_edge(edge=edge, data=data)

    # Assert
    assert isinstance(message, LocalMessage)
    assert message.source_id == "source_003"
    assert message.destination_id == "target_003"
    assert message.function_name == "perform_action"
    assert message.values == {"param_name": None}  # Parameter name exists but data is None
    assert message.target_event_id == "event_789"
    assert message.target_event_data is None


def test_create_from_edge_invalid_edge():
    # Arrange
    edge = None
    data = {"key": "value"}

    # Act & Assert
    with pytest.raises(AttributeError):
        LocalMessageFactory.create_from_edge(edge=edge, data=data)
