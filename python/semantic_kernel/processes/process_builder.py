# Copyright (c) Microsoft. All rights reserved.

import contextlib
import inspect
from collections.abc import Callable
from copy import copy
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import Field

from semantic_kernel.exceptions.process_exceptions import ProcessInvalidConfigurationException
from semantic_kernel.processes.kernel_process.kernel_process_function_target import KernelProcessFunctionTarget
from semantic_kernel.processes.kernel_process.kernel_process_state import KernelProcessState
from semantic_kernel.processes.kernel_process.kernel_process_step_info import KernelProcessStepInfo
from semantic_kernel.processes.process_edge_builder import ProcessEdgeBuilder
from semantic_kernel.processes.process_function_target_builder import ProcessFunctionTargetBuilder
from semantic_kernel.processes.process_step_builder import ProcessStepBuilder
from semantic_kernel.processes.process_step_edge_builder import ProcessStepEdgeBuilder
from semantic_kernel.processes.process_types import TState, TStep
from semantic_kernel.processes.step_utils import get_fully_qualified_name
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess


@experimental
class ProcessBuilder(ProcessStepBuilder):
    """A builder for a process."""

    entry_steps: list["ProcessStepBuilder"] = Field(default_factory=list)
    external_event_target_map: dict[str, "ProcessFunctionTargetBuilder"] = Field(default_factory=dict)
    has_parent_process: bool = False

    steps: list["ProcessStepBuilder"] = Field(default_factory=list)
    factories: dict[str, Callable] = Field(default_factory=dict)

    def add_step(
        self,
        step_type: type[TStep],
        name: str | None = None,
        initial_state: TState | None = None,
        factory_function: Callable | None = None,
        **kwargs,
    ) -> ProcessStepBuilder[TState, TStep]:
        """Register a step type with optional constructor arguments.

        Args:
            step_type: The step type.
            name: The name of the step. Defaults to None.
            initial_state: The initial state of the step. Defaults to None.
            factory_function: The factory function. Allows for a callable that is used to create the step instance
                that may have complex dependencies that cannot be JSON serialized or deserialized. Defaults to None.
            kwargs: Additional keyword arguments.

        Returns:
            The process step builder.
        """
        if not inspect.isclass(step_type):
            raise ProcessInvalidConfigurationException(
                f"Expected a class type, but got an instance of {type(step_type).__name__}"
            )

        if factory_function:
            fq_name = get_fully_qualified_name(step_type)
            self.factories[fq_name] = factory_function

        name = name or step_type.__name__
        process_step_builder = ProcessStepBuilder(type=step_type, name=name, initial_state=initial_state, **kwargs)
        self.steps.append(process_step_builder)

        return process_step_builder

    def add_step_from_process(self, kernel_process: "ProcessBuilder") -> "ProcessBuilder":
        """Adds a step from the given process."""
        kernel_process.has_parent_process = True
        self.steps.append(kernel_process)
        return kernel_process

    def resolve_function_target(
        self, function_name: str | None, parameter_name: str | None
    ) -> KernelProcessFunctionTarget:
        """Resolves the function target."""
        targets = []
        for step in self.entry_steps:
            with contextlib.suppress(ValueError):
                targets.append(step.resolve_function_target(function_name, parameter_name))

        if len(targets) == 0:
            raise ValueError(f"No targets found for function '{function_name}.{parameter_name}'")
        if len(targets) > 1:
            raise ValueError(f"Multiple targets found for function '{function_name}.{parameter_name}'")

        return targets[0]

    def where_input_event_is(self, event_id: str | Enum) -> "ProcessFunctionTargetBuilder":
        """Filters the input event."""
        event_id_str: str = event_id.value if isinstance(event_id, Enum) else event_id

        if event_id_str not in self.external_event_target_map:
            raise ValueError(f"The process named '{self.name}' does not expose an event with Id '{event_id_str}'")

        target = self.external_event_target_map[event_id_str]
        target = copy(target)
        target.step = self
        target.target_event_id = event_id_str
        return target

    def on_input_event(self, event_id: str | Enum) -> "ProcessEdgeBuilder":  # type: ignore
        """Creates a new ProcessEdgeBuilder for the input event."""
        from semantic_kernel.processes.process_builder import ProcessBuilder  # noqa: F401

        ProcessEdgeBuilder.model_rebuild()

        event_id_str: str = event_id.value if isinstance(event_id, Enum) else event_id

        return ProcessEdgeBuilder(source=self, event_id=event_id_str)

    def link_to(self, event_id: str, edge_builder: ProcessStepEdgeBuilder) -> None:
        """Links to the given event ID."""
        if edge_builder.target is None:
            raise ValueError("Target must be set before linking")
        self.entry_steps.append(edge_builder.source)
        self.external_event_target_map[event_id] = edge_builder.target
        super().link_to(event_id, edge_builder)

    def build_step(self) -> KernelProcessStepInfo:
        """Builds the process step."""
        # The process is a step so we can return the step info directly
        return self.build()

    def build(self) -> "KernelProcess":
        """Builds the KernelProcess."""
        from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess

        built_edges = {key: [edge.build() for edge in edges] for key, edges in self.edges.items()}
        built_steps = [step.build_step() for step in self.steps]
        process_state = KernelProcessState(name=self.name, id=self.id if self.has_parent_process else None)
        return KernelProcess(state=process_state, steps=built_steps, edges=built_edges, factories=self.factories)
