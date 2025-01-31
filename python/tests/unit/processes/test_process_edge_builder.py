# Copyright (c) Microsoft. All rights reserved.


from unittest.mock import MagicMock

import pytest

from semantic_kernel.processes.process_builder import ProcessBuilder
from semantic_kernel.processes.process_edge_builder import ProcessEdgeBuilder
from semantic_kernel.processes.process_function_target_builder import (
    ProcessFunctionTargetBuilder,
)
from semantic_kernel.processes.process_step_builder import ProcessStepBuilder
from semantic_kernel.processes.process_step_edge_builder import ProcessStepEdgeBuilder


@pytest.fixture(scope="function", autouse=True)
def rebuild_model():
    """Fixture to rebuild the model before each test."""
    from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata  # noqa: F401
    from semantic_kernel.processes.process_builder import ProcessBuilder  # noqa: F401

    ProcessEdgeBuilder.model_rebuild()


def test_initialization():
    from semantic_kernel.processes.process_builder import ProcessBuilder  # noqa: F401

    ProcessEdgeBuilder.model_rebuild()

    # Arrange
    source = MagicMock(spec=ProcessBuilder)
    event_id = "event_001"

    # Act
    edge_builder = ProcessEdgeBuilder(source=source, event_id=event_id)

    # Assert
    assert edge_builder.source == source
    assert edge_builder.event_id == event_id
    assert edge_builder.target is None


def test_send_event_to_with_target():
    # Arrange
    source = MagicMock(spec=ProcessBuilder)
    source.link_to = MagicMock()
    target = MagicMock(spec=ProcessFunctionTargetBuilder)
    event_id = "event_002"
    edge_builder = ProcessEdgeBuilder(source=source, event_id=event_id)

    # Act
    result = edge_builder.send_event_to(target)

    # Assert
    assert edge_builder.target == target
    assert isinstance(result, ProcessEdgeBuilder)
    linked_edge_builder = source.link_to.call_args[0][1]
    assert isinstance(linked_edge_builder, ProcessStepEdgeBuilder)
    assert linked_edge_builder.event_id == event_id
    assert linked_edge_builder.source == source
    assert linked_edge_builder.target == target


def test_send_event_to_with_step_builder():
    # Arrange
    source = MagicMock(spec=ProcessBuilder)
    source.link_to = MagicMock()
    target_step = MagicMock(spec=ProcessStepBuilder)
    target_step.resolve_function_target.return_value = MagicMock(
        function_name="process_data", parameter_name="input_param"
    )
    event_id = "event_003"
    edge_builder = ProcessEdgeBuilder(source=source, event_id=event_id)

    # Act
    result = edge_builder.send_event_to(target_step, parameter_name="input_param")

    # Assert
    assert isinstance(edge_builder.target, ProcessFunctionTargetBuilder)
    assert edge_builder.target.step == target_step
    assert edge_builder.target.parameter_name == "input_param"
    assert isinstance(result, ProcessEdgeBuilder)

    # Capture the ProcessStepEdgeBuilder that should have been linked
    linked_edge_builder = source.link_to.call_args[0][1]
    assert isinstance(linked_edge_builder, ProcessStepEdgeBuilder)
    assert linked_edge_builder.event_id == event_id
    assert linked_edge_builder.source == source
    assert linked_edge_builder.target == edge_builder.target


def test_send_event_to_step_with_multiple_functions():
    from semantic_kernel.functions.kernel_function_metadata import (
        KernelFunctionMetadata,
    )  # noqa: F401

    # Arrange
    source = MagicMock(spec=ProcessBuilder)
    source.link_to = MagicMock()

    target_step = ProcessStepBuilder(name="test_step")
    target_step.functions_dict = {
        "func_1": MagicMock(spec=KernelFunctionMetadata),
        "func_2": MagicMock(spec=KernelFunctionMetadata),
    }

    event_id = "event_004"
    edge_builder = ProcessEdgeBuilder(source=source, event_id=event_id)

    # Act - Create edges to both functions in the step
    result1 = edge_builder.send_event_to(target_step, function_name="func_1", parameter_name="input_param1")
    result2 = edge_builder.send_event_to(target_step, function_name="func_2", parameter_name="input_param2")

    # Assert
    # Verify both edges were created
    assert len(source.link_to.call_args_list) == 2

    # Check first edge
    first_edge = source.link_to.call_args_list[0][0][1]
    assert isinstance(first_edge, ProcessStepEdgeBuilder)
    assert first_edge.target.function_name == "func_1"
    assert first_edge.target.parameter_name == "input_param1"
    assert first_edge.target.step == target_step
    assert isinstance(result1, ProcessEdgeBuilder)

    # Check second edge
    second_edge = source.link_to.call_args_list[1][0][1]
    assert isinstance(second_edge, ProcessStepEdgeBuilder)
    assert second_edge.target.function_name == "func_2"
    assert second_edge.target.parameter_name == "input_param2"
    assert second_edge.target.step == target_step
    assert isinstance(result2, ProcessEdgeBuilder)


def test_send_event_to_creates_step_edge():
    # Arrange
    source = MagicMock(spec=ProcessBuilder)
    source.link_to = MagicMock()
    target = MagicMock(spec=ProcessFunctionTargetBuilder)
    event_id = "event_005"
    edge_builder = ProcessEdgeBuilder(source=source, event_id=event_id)

    # Act
    result = edge_builder.send_event_to(target)

    # Assert
    assert edge_builder.target == target
    assert isinstance(result, ProcessEdgeBuilder)
    source.link_to.assert_called_once()
    assert isinstance(source.link_to.call_args[0][1], ProcessStepEdgeBuilder)
    assert source.link_to.call_args[0][1].event_id == event_id


def test_send_event_to_raises_error_on_invalid_target():
    # Arrange
    source = MagicMock(spec=ProcessBuilder)
    event_id = "event_006"
    edge_builder = ProcessEdgeBuilder(source=source, event_id=event_id)

    # Act & Assert
    with pytest.raises(TypeError):
        edge_builder.send_event_to(None)
