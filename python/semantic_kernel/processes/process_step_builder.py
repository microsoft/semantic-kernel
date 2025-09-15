# Copyright (c) Microsoft. All rights reserved.

import logging
import uuid
from enum import Enum
from typing import TYPE_CHECKING, Any, Generic

from pydantic import Field

from semantic_kernel.exceptions.kernel_exceptions import KernelException
from semantic_kernel.exceptions.process_exceptions import ProcessInvalidConfigurationException
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.processes.kernel_process.kernel_process_function_target import KernelProcessFunctionTarget
from semantic_kernel.processes.kernel_process.kernel_process_step import KernelProcessStep
from semantic_kernel.processes.kernel_process.kernel_process_step_info import KernelProcessStepInfo
from semantic_kernel.processes.kernel_process.kernel_process_step_state import KernelProcessStepState
from semantic_kernel.processes.kernel_process.kernel_process_step_state_metadata import KernelProcessStepStateMetadata
from semantic_kernel.processes.process_state_metadata_utils import extract_process_step_metadata_from_type
from semantic_kernel.processes.process_types import TState, TStep, get_generic_state_type
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from semantic_kernel.functions import KernelFunctionMetadata
    from semantic_kernel.kernel import Kernel
    from semantic_kernel.processes.process_step_edge_builder import ProcessStepEdgeBuilder

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class ProcessStepBuilder(KernelBaseModel, Generic[TState, TStep]):
    """A builder for a process step."""

    id: str | None = None
    name: str
    edges: dict[str, list[Any]] = Field(default_factory=dict)
    functions_dict: dict[str, "KernelFunctionMetadata"] = Field(default_factory=dict)
    event_namespace: str
    function_type: type[TStep] | None = None
    initial_state: TState | None = None
    aliases: list[str] = Field(default_factory=list)

    def __init__(
        self,
        name: str,
        type: type[TStep] | None = None,
        initial_state: TState | None = None,
        aliases: list[str] | None = None,
        **kwargs,
    ):
        """Initialize the ProcessStepBuilder with a step class type and name."""
        from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata  # noqa: F401

        if not name or not name.strip():
            raise ValueError("Name cannot be null or empty")

        id = uuid.uuid4().hex

        event_namespace = f"{name}_{id}"

        functions_dict = {}
        if type:
            functions_dict = self.get_function_metadata_map(type, name, kwargs.get("kernel"))

        super().__init__(
            name=name,
            function_type=type,
            event_namespace=event_namespace,
            id=id,
            functions_dict=functions_dict,
            initial_state=initial_state,
            aliases=aliases or [],
            **kwargs,
        )

    def on_input_event(self, event_id: str | Enum) -> "ProcessStepEdgeBuilder":
        """Creates a new ProcessStepEdgeBuilder for the input event."""
        from semantic_kernel.processes.process_step_edge_builder import ProcessStepEdgeBuilder

        event_id_str: str = event_id.value if isinstance(event_id, Enum) else event_id

        return ProcessStepEdgeBuilder(source=self, event_id=event_id_str)

    def on_event(self, event_id: str | Enum) -> "ProcessStepEdgeBuilder":
        """Creates a new ProcessStepEdgeBuilder for the event."""
        from semantic_kernel.processes.process_step_edge_builder import ProcessStepEdgeBuilder

        event_id_str: str = event_id.value if isinstance(event_id, Enum) else event_id

        scoped_event_id = self.get_scoped_event_id(event_id_str)
        return ProcessStepEdgeBuilder(source=self, event_id=scoped_event_id)

    def resolve_function_target(
        self, function_name: str | None, parameter_name: str | None
    ) -> KernelProcessFunctionTarget:
        """Resolves the function target for the given function name and parameter name."""
        verified_function_name = function_name
        verified_parameter_name = parameter_name

        if not self.functions_dict:
            raise KernelException(f"The target step {self.name} has no functions.")

        # Handle null or whitespace function name
        if not verified_function_name or verified_function_name.strip() == "":
            if len(self.functions_dict) > 1:
                raise KernelException(
                    "The target step has more than one function, so a function name must be provided."
                )

            # Only one function is available; use its name
            verified_function_name = next(iter(self.functions_dict.keys()))

        # Verify that the target function exists
        if verified_function_name not in self.functions_dict:
            raise KernelException(f"The function {verified_function_name} does not exist on step {self.name}")

        # Get function parameters using inspect
        kernel_function_metadata = self.functions_dict[verified_function_name]

        if verified_parameter_name is None:
            # Exclude parameters of type KernelProcessStepContext
            undetermined_parameters = [
                p for p in kernel_function_metadata.parameters if p.type_ != "KernelProcessStepContext"
            ]

            if len(undetermined_parameters) > 1:
                raise KernelException(
                    f"The function {verified_function_name} on step {self.name} has more than one parameter, "
                    "so a parameter name must be provided."
                )

            # We can infer the parameter name from the function metadata
            if len(undetermined_parameters) == 1:
                parameter_name = undetermined_parameters[0].name
                verified_parameter_name = parameter_name

        return KernelProcessFunctionTarget(
            step_id=self.id, function_name=verified_function_name, parameter_name=verified_parameter_name
        )

    def get_scoped_event_id(self, event_id: str) -> str:
        """Returns the scoped event ID."""
        return f"{self.event_namespace}.{event_id}"

    def get_subtype_of_stateful_step(self, type_to_check):
        """Check if the provided type is a subclass of a generic KernelProcessStep and return its generic type if so."""
        while type_to_check is not None and type_to_check is not object:
            if hasattr(type_to_check, "__orig_bases__"):
                for base in type_to_check.__orig_bases__:
                    if hasattr(base, "__origin__") and base.__origin__ == KernelProcessStep:
                        return base  # Return the generic type itself
            type_to_check = type_to_check.__base__

        return None

    def build_step(self, state_metadata: KernelProcessStepStateMetadata | None = None) -> KernelProcessStepInfo:
        """Builds the process step."""
        step_cls = self.function_type
        if step_cls is None:
            raise ProcessInvalidConfigurationException("function_type is not set.")

        step_metadata_attr = extract_process_step_metadata_from_type(step_cls)
        version = step_metadata_attr.version

        t_state = get_generic_state_type(step_cls)

        state_object: KernelProcessStepState | None = None

        if t_state is not None:
            # The step is a KernelProcessStep with user-defined state
            parsed_state_from_metadata = None
            if state_metadata and state_metadata.state is not None:
                candidate = state_metadata.state
                if isinstance(candidate, dict):
                    try:
                        parsed_state_from_metadata = (
                            t_state(**candidate) if hasattr(t_state, "__fields__") else t_state()
                        )
                    except Exception as ex:
                        raise KernelException(
                            f"The initial state provided for step {self.name} is not valid "
                            f" JSON or cannot be parsed: {ex}"
                        )
                else:
                    if isinstance(candidate, t_state):
                        parsed_state_from_metadata = candidate
                    else:
                        raise KernelException(
                            f"The initial state for step {self.name} is not the "
                            f"correct type. Expected {t_state.__name__}."
                        )

            actual_state = parsed_state_from_metadata if parsed_state_from_metadata is not None else self.initial_state

            if actual_state is not None and not isinstance(actual_state, t_state):
                raise ProcessInvalidConfigurationException(
                    f"The initial state provided for step {self.name} is not of the correct type. "
                    f"The expected type is {t_state.__name__}."
                )

            if actual_state is None:
                actual_state = t_state() if hasattr(t_state, "__fields__") else t_state

            state_object = KernelProcessStepState[t_state](  # type: ignore
                name=self.name, id=self.id, version=version, state=actual_state
            )
        else:
            # The step is a KernelProcessStep with no user-defined state
            if self.initial_state is not None:
                raise ProcessInvalidConfigurationException(
                    f"An initial state was provided for step {self.name}, but the step does not accept a state."
                )
            if state_metadata and state_metadata.state is not None:
                state_object = KernelProcessStepState(
                    name=self.name, id=self.id, version=version, state=state_metadata.state
                )
            else:
                state_object = KernelProcessStepState(name=self.name, id=self.id, version=version, state=None)

        built_edges = {event_id: [edge.build() for edge in edges_list] for event_id, edges_list in self.edges.items()}

        return KernelProcessStepInfo(inner_step_type=step_cls, state=state_object, output_edges=built_edges)

    def on_function_result(self, function_name: str | Enum) -> "ProcessStepEdgeBuilder":
        """Creates a new ProcessStepEdgeBuilder for the function result.

        Args:
            function_name: The function name as a string or Enum.

        Returns:
            ProcessStepEdgeBuilder: The ProcessStepEdgeBuilder instance.
        """
        function_name_str: str = function_name.value if isinstance(function_name, Enum) else function_name

        return self.on_event(f"{function_name_str}.OnResult")

    def get_function_metadata_map(
        self, plugin_type, name: str | None = None, kernel: "Kernel | None" = None
    ) -> dict[str, "KernelFunctionMetadata"]:
        """Returns a mapping of function names to their metadata."""
        from semantic_kernel.kernel import Kernel

        if not kernel:
            kernel = Kernel()

        step_instance = plugin_type()

        functions_dict = {}
        plugin_name = name or self.__class__.__name__
        plugin_functions = kernel.add_plugin(step_instance, plugin_name)
        for func_name, func in plugin_functions.functions.items():
            functions_dict[func_name] = func.metadata
        return functions_dict

    def link_to(self, event_id: str, edge_builder: "ProcessStepEdgeBuilder") -> None:
        """Links an event ID to a ProcessStepEdgeBuilder."""
        edges = self.edges.get(event_id)

        if edges is None:
            edges = []
            self.edges[event_id] = edges

        # Add the edge builder to the list
        edges.append(edge_builder)
