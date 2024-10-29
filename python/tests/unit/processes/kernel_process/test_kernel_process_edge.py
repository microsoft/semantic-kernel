# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.processes.kernel_process.kernel_process_edge import KernelProcessEdge
from semantic_kernel.processes.kernel_process.kernel_process_function_target import KernelProcessFunctionTarget


def test_initialization():
    """Test initialization of KernelProcessEdge with valid input."""
    source_step_id = "step_1"
    output_target = KernelProcessFunctionTarget(
        step_id="step_2", function_name="process_data", parameter_name="input_data", target_event_id="event_1"
    )
    edge = KernelProcessEdge(source_step_id=source_step_id, output_target=output_target)

    assert edge.source_step_id == source_step_id
    assert edge.output_target == output_target


def test_initialization_with_none_parameter_name():
    """Test KernelProcessEdge initialization with a target having None as parameter_name."""
    source_step_id = "step_1"
    output_target = KernelProcessFunctionTarget(
        step_id="step_2", function_name="process_data", parameter_name=None, target_event_id="event_1"
    )
    edge = KernelProcessEdge(source_step_id=source_step_id, output_target=output_target)

    assert edge.source_step_id == source_step_id
    assert edge.output_target.parameter_name is None


def test_initialization_with_none_target_event_id():
    """Test KernelProcessEdge initialization with a target having None as target_event_id."""
    source_step_id = "step_1"
    output_target = KernelProcessFunctionTarget(
        step_id="step_2", function_name="process_data", parameter_name="input_data", target_event_id=None
    )
    edge = KernelProcessEdge(source_step_id=source_step_id, output_target=output_target)

    assert edge.source_step_id == source_step_id
    assert edge.output_target.target_event_id is None


def test_initialization_with_empty_strings():
    """Test KernelProcessEdge initialization with empty strings for step_id and function_name."""
    source_step_id = ""
    output_target = KernelProcessFunctionTarget(step_id="", function_name="", parameter_name="", target_event_id="")
    edge = KernelProcessEdge(source_step_id=source_step_id, output_target=output_target)

    assert edge.source_step_id == ""
    assert edge.output_target.step_id == ""
    assert edge.output_target.function_name == ""
    assert edge.output_target.parameter_name == ""
    assert edge.output_target.target_event_id == ""
