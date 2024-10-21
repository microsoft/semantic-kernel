# Copyright (c) Microsoft. All rights reserved.

import logging
import uuid
from typing import TYPE_CHECKING, Any, Generic

from pydantic import Field

from semantic_kernel.functions import KernelFunctionMetadata
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.processes.kernel_process.kernel_process_function_target import KernelProcessFunctionTarget
from semantic_kernel.processes.kernel_process.kernel_process_step import KernelProcessStep
from semantic_kernel.processes.kernel_process.kernel_process_step_info import KernelProcessStepInfo
from semantic_kernel.processes.kernel_process.kernel_process_step_state import KernelProcessStepState
from semantic_kernel.processes.process_types import TState, TStep
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.kernel import Kernel
    from semantic_kernel.processes.process_step_edge_builder import ProcessStepEdgeBuilder

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class ProcessStepBuilder(KernelBaseModel, Generic[TState, TStep]):
    """A builder for a process step."""

    id: str | None = None
    name: str
    edges: dict[str, list[Any]] = Field(default_factory=dict)
    functions_dict: dict[str, "KernelFunctionMetadata"] = Field(default_factory=dict)
    event_namespace: str
    function_type: type[TStep] | None = None
    initial_state: TState | None = None

    def __init__(self, name: str, type: type[TStep] | None = None, initial_state: TState | None = None, **kwargs):
        """Initialize the ProcessStepBuilder with a step class type and name."""
        if not name or not name.strip():
            raise ValueError("Name cannot be null or empty")

        # Set a unique ID for the step
        id = uuid.uuid4().hex

        # Set the event namespace based on name and ID
        event_namespace = f"{name}_{id}"

        functions_dict = {}
        if type:
            # Initialize functions dictionary by fetching the function metadata
            functions_dict = self.get_function_metadata_map(type, name, kwargs.get("kernel", None))

        # Call the parent Pydantic BaseModel constructor using super()
        super().__init__(
            name=name,
            function_type=type,
            event_namespace=event_namespace,
            id=id,
            functions_dict=functions_dict,
            initial_state=initial_state,
            **kwargs,
        )

    def on_input_event(self, event_id: str) -> "ProcessStepEdgeBuilder":
        """Creates a new ProcessStepEdgeBuilder for the input event."""
        from semantic_kernel.processes.process_step_edge_builder import ProcessStepEdgeBuilder

        return ProcessStepEdgeBuilder(source=self, event_id=event_id)

    def on_event(self, event_id: str) -> "ProcessStepEdgeBuilder":
        """Creates a new ProcessStepEdgeBuilder for the event."""
        from semantic_kernel.processes.process_step_edge_builder import ProcessStepEdgeBuilder

        scoped_event_id = self.get_scoped_event_id(event_id)
        return ProcessStepEdgeBuilder(source=self, event_id=scoped_event_id)

    def resolve_function_target(
        self, function_name: str | None, parameter_name: str | None
    ) -> KernelProcessFunctionTarget:
        """Resolves the function target for the given function name and parameter name."""
        if not self.functions_dict:
            raise ValueError(f"No functions found on step {self.name}")

        if function_name is None:
            if len(self.functions_dict) > 1:
                raise ValueError("Multiple functions available, function name must be provided")
            function_name = next(iter(self.functions_dict))

        return KernelProcessFunctionTarget(step_id=self.id, function_name=function_name, parameter_name=parameter_name)

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

    def build_step(self) -> "KernelProcessStepInfo":
        """Builds the process step."""
        # Use the state attribute directly if it is set.
        if self.initial_state is not None:
            # Assume the state is already the correct type.
            state_object = KernelProcessStepState[TState](name=self.name, id=self.id, state=self.initial_state)
        else:
            # If no state is provided, initialize an empty state.
            state_object = KernelProcessStepState[TState](name=self.name, id=self.id, state=None)

        # Build the edges based on the current step's edge definitions.
        built_edges = {event_id: [edge.build() for edge in edges] for event_id, edges in self.edges.items()}

        # Return an instance of KernelProcessStepInfo with the built state and edges.
        assert self.function_type  # nosec
        return KernelProcessStepInfo(inner_step_type=self.function_type, state=state_object, output_edges=built_edges)

    def on_function_result(self, function_name: str) -> "ProcessStepEdgeBuilder":
        """Creates a new ProcessStepEdgeBuilder for the function result."""
        return self.on_event(f"{function_name}.OnResult")

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
        # Retrieve the list of edges for the event_id, or create a new list if it doesn't exist
        edges = self.edges.get(event_id)

        if edges is None:
            # If the list doesn't exist, initialize it and add it to the dictionary
            edges = []
            self.edges[event_id] = edges

        # Add the edge builder to the list
        edges.append(edge_builder)
