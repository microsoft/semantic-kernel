# Copyright (c) Microsoft. All rights reserved.

import contextlib
import inspect
from copy import copy
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import Field

from semantic_kernel.exceptions.process_exceptions import ProcessInvalidConfigurationException
from semantic_kernel.processes.kernel_process.kernel_process_function_target import KernelProcessFunctionTarget
from semantic_kernel.processes.kernel_process.kernel_process_state import KernelProcessState
from semantic_kernel.processes.kernel_process.kernel_process_state_metadata import KernelProcessStateMetadata
from semantic_kernel.processes.kernel_process.kernel_process_step_info import KernelProcessStepInfo
from semantic_kernel.processes.kernel_process.kernel_process_step_state_metadata import KernelProcessStepStateMetadata
from semantic_kernel.processes.process_edge_builder import ProcessEdgeBuilder
from semantic_kernel.processes.process_function_target_builder import ProcessFunctionTargetBuilder
from semantic_kernel.processes.process_state_metadata_utils import to_process_state_metadata
from semantic_kernel.processes.process_step_builder import ProcessStepBuilder
from semantic_kernel.processes.process_step_edge_builder import ProcessStepEdgeBuilder
from semantic_kernel.processes.process_types import TState, TStep
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess


@experimental_class
class ProcessBuilder(ProcessStepBuilder):
    """A builder for a process."""

    entry_steps: list["ProcessStepBuilder"] = Field(default_factory=list)
    external_event_target_map: dict[str, "ProcessFunctionTargetBuilder"] = Field(default_factory=dict)
    has_parent_process: bool = False
    version: str = "v1"

    steps: list["ProcessStepBuilder"] = Field(default_factory=list)

    def add_step(
        self,
        step_type: type[TStep],
        name: str | None = None,
        initial_state: TState | None = None,
        aliases: list[str] | None = None,
        **kwargs,
    ) -> ProcessStepBuilder[TState, TStep]:
        """Register a step type with optional constructor arguments."""
        if not inspect.isclass(step_type):
            raise ProcessInvalidConfigurationException(
                f"Expected a class type, but got an instance of {type(step_type).__name__}"
            )

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

    def build_step(self, state_metadata: KernelProcessStepStateMetadata | None = None) -> KernelProcessStepInfo:
        """Builds the process step."""
        # The process is a step so we can return the step info directly
        return self.build(state_metadata=state_metadata)

    def build(self, state_metadata: KernelProcessStateMetadata | None = None) -> "KernelProcess":
        """Builds the KernelProcess."""
        from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess

        # Build the edges first
        built_edges = {key: [edge.build() for edge in edges] for key, edges in self.edges.items()}

        # Build the steps and inject initial state if any is provided
        built_steps = self._build_with_state_metadata(self, state_metadata)

        # Create the process
        state = KernelProcessState(
            name=self.name, version=self.version, id=self.id if self.has_parent_process else None
        )
        return KernelProcess(state, built_steps, built_edges)

    def _build_with_state_metadata(
        self, process_builder: "ProcessBuilder", state_metadata: KernelProcessStateMetadata | None
    ) -> list[KernelProcessStepInfo]:
        """Builds the steps with the given state metadata."""
        built_steps: list[KernelProcessStepInfo] = []

        sanitized_metadata = None
        if state_metadata is not None:
            sanitized_metadata = self._sanitize_process_state_metadata(state_metadata, process_builder.steps)

        for step in process_builder.steps:
            steps_state_object = None
            if sanitized_metadata and sanitized_metadata.steps_state:
                steps_state_object = sanitized_metadata.steps_state.get(step.name)

            # If we have a state object for this step, build with state
            if steps_state_object is not None:
                built_steps.append(step.build_step(steps_state_object))
            else:
                built_steps.append(step.build_step())

        return built_steps

    def _sanitize_process_state_metadata(
        self, state_metadata: KernelProcessStateMetadata, step_builders: list[ProcessStepBuilder]
    ) -> KernelProcessStateMetadata:
        """Sanitize the process state metadata by fixing aliases and version mismatches."""
        sanitized_state: KernelProcessStateMetadata = copy(state_metadata)

        # If there's no steps_state, nothing to fix
        if sanitized_state.steps_state is None:
            return sanitized_state

        for step in step_builders:
            # 1) find matching key name with exact match or by alias match
            step_aliases = step.aliases if hasattr(step, "aliases") else []
            step_key = None

            if step.name in sanitized_state.steps_state:
                step_key = step.name
            else:
                for alias in step_aliases:
                    if alias in sanitized_state.steps_state:
                        step_key = alias
                        break

            # 2) stepKey match found
            if step_key is not None:
                # Build the "current version state metadata" for the step
                current_version_state_metadata = to_process_state_metadata(step.build_step())

                saved_state_metadata: KernelProcessStepStateMetadata = sanitized_state.steps_state.get(step_key)
                if saved_state_metadata is not None and step_key != step.name:
                    # Compare versions
                    if saved_state_metadata.version_info == current_version_state_metadata.version_info:
                        # key mismatch only, but same version
                        sanitized_state.steps_state[step.name] = saved_state_metadata
                    else:
                        # version mismatch - check if migration logic is in place
                        if isinstance(step, ProcessBuilder):
                            # Recursively sanitize the child process state
                            # Here we assume saved_state_metadata is indeed a KernelProcessStateMetadata
                            # (the user is responsible for ensuring the JSON actually matches).
                            sanitized_subprocess_state = self.sanitize_process_state_metadata(
                                saved_state_metadata,
                                step.steps,  # type: ignore
                            )
                            sanitized_state.steps_state[step.name] = sanitized_subprocess_state
                        else:
                            # no compatible state found, migrating id only
                            # We create a brand new KernelProcessStepStateMetadata with
                            # just the name + id
                            sanitized_state.steps_state[step.name] = KernelProcessStepStateMetadata(
                                name=step.name,
                                id=step.id,
                            )

                    # Either way, we finalize by updating the new step’s name
                    # and removing the old key
                    sanitized_state.steps_state[step.name].name = step.name
                    del sanitized_state.steps_state[step_key]

        return sanitized_state
