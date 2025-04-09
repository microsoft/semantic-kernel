# Copyright (c) Microsoft. All rights reserved.


from unittest.mock import MagicMock

import pytest

from semantic_kernel.processes.kernel_process.kernel_process_edge import KernelProcessEdge
from semantic_kernel.processes.kernel_process.kernel_process_function_target import KernelProcessFunctionTarget
from semantic_kernel.processes.process_function_target_builder import ProcessFunctionTargetBuilder
from semantic_kernel.processes.process_step_builder import ProcessStepBuilder
from semantic_kernel.processes.process_step_edge_builder import ProcessStepEdgeBuilder


def test_initialization():
    # Arrange
    source = MagicMock(spec=ProcessStepBuilder)
    event_id = "event_001"

    # Act
    edge_builder = ProcessStepEdgeBuilder(source=source, event_id=event_id)

    # Assert
    assert edge_builder.source == source
    assert edge_builder.event_id == event_id
    assert edge_builder.target is None


def test_send_event_to():
    # Arrange
    source = MagicMock(spec=ProcessStepBuilder)
    source.link_to = MagicMock()
    target = MagicMock(spec=ProcessFunctionTargetBuilder)
    event_id = "event_002"
    edge_builder = ProcessStepEdgeBuilder(source=source, event_id=event_id)

    # Act
    edge_builder.send_event_to(target)

    # Assert
    assert edge_builder.target == target
    source.link_to.assert_called_once_with(event_id, edge_builder)


def test_send_event_to_step_builder_input():
    # Arrange
    source = MagicMock(spec=ProcessStepBuilder)
    source.link_to = MagicMock()

    target = MagicMock(spec=ProcessStepBuilder)
    target.resolve_function_target = MagicMock(
        return_value=MagicMock(function_name="mock_function_name", parameter_name="provided_parameter_name")
    )

    event_id = "event_003"
    edge_builder = ProcessStepEdgeBuilder(source=source, event_id=event_id)

    # Act
    edge_builder.send_event_to(target, parameter_name="provided_parameter_name")

    # Assert
    assert edge_builder.target.step == target
    assert edge_builder.target.parameter_name == "provided_parameter_name"
    source.link_to.assert_called_once_with(event_id, edge_builder)


def test_send_event_to_creates_target():
    # Arrange
    source = MagicMock(spec=ProcessStepBuilder)
    source.link_to = MagicMock()
    target_step = MagicMock(spec=ProcessStepBuilder)
    target_step.resolve_function_target.return_value = MagicMock(
        function_name="process_data", parameter_name="input_param"
    )
    event_id = "event_003"
    edge_builder = ProcessStepEdgeBuilder(source=source, event_id=event_id)

    # Act
    edge_builder.send_event_to(target_step, parameter_name="input_param")

    # Assert
    assert isinstance(edge_builder.target, ProcessFunctionTargetBuilder)
    assert edge_builder.target.step == target_step
    assert edge_builder.target.function_name == "process_data"
    assert edge_builder.target.parameter_name == "input_param"
    source.link_to.assert_called_once_with(event_id, edge_builder)


def test_stop_process():
    # Arrange
    source = MagicMock(spec=ProcessStepBuilder)
    source.link_to = MagicMock()
    event_id = "event_004"
    edge_builder = ProcessStepEdgeBuilder(source=source, event_id=event_id)

    # Act
    edge_builder.stop_process()

    # Assert
    assert edge_builder.target is not None
    assert edge_builder.target.function_name == "END"
    source.link_to.assert_called_once_with("END", edge_builder)


def test_build():
    # Arrange
    source = MagicMock(spec=ProcessStepBuilder)
    source.id = "source_step_id"
    source.name = "source_step_name"
    target = MagicMock(spec=ProcessFunctionTargetBuilder)
    target.build = MagicMock(return_value=MagicMock(spec=KernelProcessFunctionTarget))
    event_id = "event_005"
    edge_builder = ProcessStepEdgeBuilder(source=source, event_id=event_id)
    edge_builder.target = target

    # Act
    edge = edge_builder.build()

    # Assert
    assert isinstance(edge, KernelProcessEdge)
    assert edge.source_step_id == source.id
    assert edge.output_target == target.build()


def test_build_missing_target():
    # Arrange
    source = MagicMock(spec=ProcessStepBuilder)
    source.id = "source_step_id"
    source.name = "source_step_name"
    event_id = "event_006"
    edge_builder = ProcessStepEdgeBuilder(source=source, event_id=event_id)

    # Act & Assert
    with pytest.raises(ValueError, match="Target must be provided"):
        edge_builder.build()


def test_send_event_to_step_builder_with_function_name():
    # Arrange
    source = MagicMock(spec=ProcessStepBuilder)
    source.link_to = MagicMock()

    target = MagicMock(spec=ProcessStepBuilder)
    target.resolve_function_target = MagicMock(
        return_value=MagicMock(function_name="mock_function_name", parameter_name="mock_parameter_name")
    )

    event_id = "event_007"
    edge_builder = ProcessStepEdgeBuilder(source=source, event_id=event_id)

    # Act
    edge_builder.send_event_to(target, parameter_name="mock_parameter_name", function_name="mock_function_name")

    # Assert
    assert edge_builder.target.step == target
    assert edge_builder.target.parameter_name == "mock_parameter_name"
    assert edge_builder.target.function_name == "mock_function_name"
    source.link_to.assert_called_once_with(event_id, edge_builder)
