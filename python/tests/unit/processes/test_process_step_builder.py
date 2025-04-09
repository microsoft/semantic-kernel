# Copyright (c) Microsoft. All rights reserved.

from enum import Enum
from unittest.mock import MagicMock

import pytest

from semantic_kernel.exceptions.kernel_exceptions import KernelException
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.processes.kernel_process.kernel_process_edge import KernelProcessEdge
from semantic_kernel.processes.kernel_process.kernel_process_function_target import KernelProcessFunctionTarget
from semantic_kernel.processes.kernel_process.kernel_process_step import KernelProcessStep
from semantic_kernel.processes.kernel_process.kernel_process_step_info import KernelProcessStepInfo
from semantic_kernel.processes.process_step_builder import ProcessStepBuilder
from semantic_kernel.processes.process_step_edge_builder import ProcessStepEdgeBuilder


class TestFunctionEnum(Enum):
    MY_FUNCTION = "my_function"


class MockKernelProcessStep(KernelProcessStep):
    """A mock class to use as a step type."""

    pass


def test_initialization():
    # Arrange
    name = "test_step"
    step_type = MockKernelProcessStep
    initial_state = MagicMock()

    # Act
    step_builder = ProcessStepBuilder(name=name, type=step_type, initial_state=initial_state)

    # Assert
    assert step_builder.name == name
    assert step_builder.function_type == step_type
    assert step_builder.initial_state == initial_state
    assert step_builder.id is not None
    assert step_builder.event_namespace.startswith(name)


def test_initialization_without_type():
    # Arrange
    name = "test_step_no_type"

    # Act
    step_builder = ProcessStepBuilder(name=name)

    # Assert
    assert step_builder.name == name
    assert step_builder.function_type is None
    assert step_builder.initial_state is None
    assert step_builder.id is not None
    assert step_builder.event_namespace.startswith(name)


def test_on_input_event():
    # Arrange
    name = "test_step"
    event_id = "event_input"
    step_builder = ProcessStepBuilder(name=name)

    # Act
    edge_builder = step_builder.on_input_event(event_id=event_id)

    # Assert
    assert isinstance(edge_builder, ProcessStepEdgeBuilder)
    assert edge_builder.source == step_builder
    assert edge_builder.event_id == event_id


def test_on_event():
    # Arrange
    name = "test_step"
    event_id = "event_action"
    step_builder = ProcessStepBuilder(name=name)

    # Act
    edge_builder = step_builder.on_event(event_id=event_id)

    # Assert
    assert isinstance(edge_builder, ProcessStepEdgeBuilder)
    assert edge_builder.source == step_builder
    assert edge_builder.event_id == f"{step_builder.event_namespace}.{event_id}"


def test_resolve_function_target_with_single_function():
    # Arrange
    name = "test_step"
    step_builder = ProcessStepBuilder(name=name)
    step_builder.functions_dict = {"process_data": MagicMock(spec=KernelFunctionMetadata)}

    # Act
    target = step_builder.resolve_function_target(function_name=None, parameter_name="input_param")

    # Assert
    assert target.function_name == "process_data"
    assert target.parameter_name == "input_param"


def test_resolve_function_target_with_multiple_functions():
    # Arrange
    name = "test_step"
    step_builder = ProcessStepBuilder(name=name)
    step_builder.functions_dict = {
        "func_1": MagicMock(spec=KernelFunctionMetadata),
        "func_2": MagicMock(spec=KernelFunctionMetadata),
    }

    # Act & Assert
    with pytest.raises(
        KernelException, match="The target step has more than one function, so a function name must be provided."
    ):
        step_builder.resolve_function_target(function_name=None, parameter_name="input_param")


def test_get_scoped_event_id():
    # Arrange
    name = "test_step"
    step_builder = ProcessStepBuilder(name=name)
    event_id = "my_event"

    # Act
    scoped_event_id = step_builder.get_scoped_event_id(event_id)

    # Assert
    assert scoped_event_id == f"{step_builder.event_namespace}.{event_id}"


def test_build_step():
    # Arrange
    name = "test_step"
    step_builder = ProcessStepBuilder(name=name, type=MockKernelProcessStep)

    edge = MagicMock(spec=KernelProcessEdge)
    built_edge = KernelProcessEdge(
        source_step_id="source_step_id",
        output_target=MagicMock(spec=KernelProcessFunctionTarget),
    )
    edge.build = MagicMock(return_value=built_edge)

    step_builder.edges = {"event_1": [edge]}

    # Act
    step_info = step_builder.build_step()

    # Assert
    assert isinstance(step_info, KernelProcessStepInfo)
    assert step_info.state.name == step_builder.name
    assert step_info.state.id == step_builder.id
    assert step_info.output_edges == {"event_1": [built_edge]}


def test_link_to():
    # Arrange
    name = "test_step"
    step_builder = ProcessStepBuilder(name=name)
    edge_builder = MagicMock(spec=ProcessStepEdgeBuilder)
    event_id = "event_1"

    # Act
    step_builder.link_to(event_id, edge_builder)

    # Assert
    assert step_builder.edges[event_id] == [edge_builder]


def test_link_to_multiple_edges():
    # Arrange
    name = "test_step"
    step_builder = ProcessStepBuilder(name=name)
    edge_builder_1 = MagicMock(spec=ProcessStepEdgeBuilder)
    edge_builder_2 = MagicMock(spec=ProcessStepEdgeBuilder)
    event_id = "event_2"

    # Act
    step_builder.link_to(event_id, edge_builder_1)
    step_builder.link_to(event_id, edge_builder_2)

    # Assert
    assert step_builder.edges[event_id] == [edge_builder_1, edge_builder_2]


@pytest.mark.parametrize(
    "function_name, expected_function_name",
    [
        ("my_function", "my_function"),
        (TestFunctionEnum.MY_FUNCTION, TestFunctionEnum.MY_FUNCTION.value),
    ],
)
def test_on_function_result(function_name, expected_function_name):
    # Arrange
    name = "test_step"
    step_builder = ProcessStepBuilder(name=name)

    # Act
    edge_builder = step_builder.on_function_result(function_name=function_name)

    # Assert
    assert isinstance(edge_builder, ProcessStepEdgeBuilder)
    assert edge_builder.source == step_builder
    assert edge_builder.event_id == f"{step_builder.event_namespace}.{expected_function_name}.OnResult"
