# Copyright (c) Microsoft. All rights reserved.
from enum import Enum

import pytest

from semantic_kernel.exceptions.process_exceptions import ProcessInvalidConfigurationException
from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess
from semantic_kernel.processes.kernel_process.kernel_process_function_target import KernelProcessFunctionTarget
from semantic_kernel.processes.kernel_process.kernel_process_step import KernelProcessStep
from semantic_kernel.processes.process_builder import ProcessBuilder
from semantic_kernel.processes.process_function_target_builder import ProcessFunctionTargetBuilder
from semantic_kernel.processes.process_step_builder import ProcessStepBuilder
from semantic_kernel.processes.process_step_edge_builder import ProcessStepEdgeBuilder
from semantic_kernel.processes.step_utils import get_fully_qualified_name


def _create_builder(name: str) -> ProcessBuilder:
    """Helper to construct a ProcessBuilder instance bypassing BaseModel required fields."""
    return ProcessBuilder.model_construct(
        name=name,
        event_namespace=f"{name}_ns",
        id="id",
        functions_dict={},
        edges={},
        entry_steps=[],
        external_event_target_map={},
        has_parent_process=False,
        steps=[],
        factories={},
    )


class DummyTarget:
    function_name = "some_function"
    parameter_name = "some_param"


class DummyStep(KernelProcessStep):
    def resolve_function_target(self, function_name, parameter_name):
        return DummyTarget()


class SampleEnum(Enum):
    """Sample enum for event IDs."""

    EVENT_A = "event_a"


def test_add_step_with_non_class_raises() -> None:
    """Test that add_step raises when a non-class is passed as step_type."""
    builder = _create_builder("testProc")
    with pytest.raises(ProcessInvalidConfigurationException) as exc_info:
        builder.add_step(123)  # type: ignore
    assert "Expected a class type" in str(exc_info.value)


def test_add_step_appends_step_and_returns_builder() -> None:
    """Test that a valid class step is appended and returned correctly."""
    builder = _create_builder("proc1")
    initial_state = {"key": "value"}
    step_builder = builder.add_step(DummyStep, name="CustomStep", initial_state=initial_state)
    assert step_builder in builder.steps
    assert step_builder.name == "CustomStep"
    assert step_builder.initial_state == initial_state


def test_add_step_with_factory_function_stores_factory() -> None:
    """Test that providing a factory function stores it in the factories dict."""
    builder = _create_builder("proc2")

    def factory_func() -> DummyStep:
        return DummyStep()

    builder.add_step(DummyStep, factory_function=factory_func)
    fqn = get_fully_qualified_name(DummyStep)
    assert fqn in builder.factories
    assert builder.factories[fqn] is factory_func


def test_where_input_event_missing_raises() -> None:
    """Test that where_input_event raises when the event ID is not registered."""
    builder = _create_builder("proc")
    with pytest.raises(ValueError) as exc_info:
        builder.where_input_event_is("nonexistent")
    assert "does not expose an event with Id" in str(exc_info.value)


def test_where_input_event_success_returns_copy() -> None:
    """Test that where_input_event returns a copy with updated step and event id."""
    builder = _create_builder("proc")
    builder.entry_steps.append(DummyStep())
    orig = ProcessFunctionTargetBuilder(builder)
    builder.external_event_target_map["evt1"] = orig

    class Evt(Enum):
        EVT1 = "evt1"

    result = builder.where_input_event_is(Evt.EVT1)
    assert result is not orig
    assert result.step is builder
    assert result.target_event_id == "evt1"


def test_on_input_event_returns_edge_builder_with_string_and_enum() -> None:
    """Test that on_input_event returns a ProcessEdgeBuilder with correct source and event_id."""

    from semantic_kernel.processes.process_builder import ProcessEdgeBuilder  # noqa: F811, I001
    from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata  # noqa: F401
    from semantic_kernel.processes.process_builder import ProcessBuilder  # noqa: F401

    ProcessEdgeBuilder.model_rebuild()

    builder = _create_builder("proc")
    eb_str = builder.on_input_event("myEvent")
    assert isinstance(eb_str, ProcessEdgeBuilder)
    assert eb_str.source is builder
    assert eb_str.event_id == "myEvent"
    eb_enum = builder.on_input_event(SampleEnum.EVENT_A)
    assert eb_enum.event_id == SampleEnum.EVENT_A.value


def test_link_to_raises_when_target_none() -> None:
    """Test that link_to raises when edge_builder.target is not set."""
    builder = _create_builder("proc")
    edge = ProcessStepEdgeBuilder(source=builder, event_id="evt")
    with pytest.raises(ValueError) as exc_info:
        builder.link_to("evt", edge)
    assert "Target must be set before linking" in str(exc_info.value)


def test_link_to_success_updates_internal_maps_and_edges() -> None:
    """Test that link_to properly updates entry_steps, external_event_target_map, and edges."""
    builder = _create_builder("proc")
    edge = ProcessStepEdgeBuilder(source=builder, event_id="evt")
    builder.entry_steps.append(DummyStep())
    target_builder = ProcessFunctionTargetBuilder(builder)
    edge.target = target_builder
    builder.link_to("evt", edge)
    assert edge.source in builder.entry_steps
    assert builder.external_event_target_map["evt"] is target_builder
    assert "evt" in builder.edges
    assert edge in builder.edges["evt"]


def test_build_with_simple_step_yields_kernel_process() -> None:
    """Test that build returns a KernelProcess with correct properties for simple steps."""
    builder = _create_builder("simpleProc")
    builder.add_step(DummyStep)
    process = builder.build()
    assert isinstance(process, KernelProcess)
    assert process.state.name == "simpleProc"
    assert process.state.id is None
    assert len(process.steps) == 1
    step_info = process.steps[0]
    assert step_info.inner_step_type is DummyStep
    assert step_info.output_edges == {}
    assert process.factories == {}


def test_resolve_function_target_no_steps_raises() -> None:
    """Test that resolve_function_target raises when there are no entry_steps."""
    builder = _create_builder("proc")
    with pytest.raises(ValueError) as exc_info:
        builder.resolve_function_target("fn", "param")
    assert "No targets found for function" in str(exc_info.value)


def test_resolve_function_target_multiple_targets_raises() -> None:
    """Test that resolve_function_target raises when multiple entry_steps return targets."""
    builder = _create_builder("proc")

    from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata  # noqa: F401
    from semantic_kernel.processes.process_builder import ProcessBuilder  # noqa: F401

    ProcessBuilder.model_rebuild()

    class FakeStep(ProcessStepBuilder):
        def __init__(self, name: str = "default_step_name"):
            super().__init__(name=name)

        def resolve_function_target(self, fn: str, pn: str) -> KernelProcessFunctionTarget:
            return KernelProcessFunctionTarget(step_id="1", function_name=fn, parameter_name=pn)

    builder.entry_steps = [FakeStep(), FakeStep()]  # type: ignore
    with pytest.raises(ValueError) as exc_info:
        builder.resolve_function_target("fn", "param")
    assert "Multiple targets found for function" in str(exc_info.value)


def test_resolve_function_target_success() -> None:
    """Test that resolve_function_target returns the single target when exactly one entry_step matches."""
    builder = _create_builder("proc")

    from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata  # noqa: F401
    from semantic_kernel.processes.process_builder import ProcessBuilder  # noqa: F401

    ProcessBuilder.model_rebuild()

    class FakeStep(ProcessStepBuilder):
        def __init__(self, name: str = "default_step_name"):
            super().__init__(name=name)

        def resolve_function_target(self, fn: str, pn: str) -> KernelProcessFunctionTarget:
            return KernelProcessFunctionTarget(step_id="1", function_name=fn, parameter_name=pn)

    builder.entry_steps = [FakeStep()]  # type: ignore
    result = builder.resolve_function_target("myFn", "myParam")
    assert isinstance(result, KernelProcessFunctionTarget)
    assert result.step_id == "1"
    assert result.function_name == "myFn"
    assert result.parameter_name == "myParam"
