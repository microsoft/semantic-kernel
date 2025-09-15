# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.processes.process_function_target_builder import ProcessFunctionTargetBuilder
from semantic_kernel.processes.process_step_builder import ProcessStepBuilder
from semantic_kernel.processes.process_step_edge_builder import ProcessStepEdgeBuilder
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from semantic_kernel.processes.process_builder import ProcessBuilder


@experimental
class ProcessEdgeBuilder(KernelBaseModel):
    """A builder for a process edge."""

    source: "ProcessBuilder"
    target: ProcessFunctionTargetBuilder | None = None
    event_id: str

    def __init__(self, source: "ProcessBuilder", event_id: str):
        """Initializes a new instance of ProcessEdgeBuilder."""
        super().__init__(source=source, event_id=event_id)  # type: ignore

    def send_event_to(
        self, target: ProcessFunctionTargetBuilder | ProcessStepBuilder, **kwargs
    ) -> "ProcessEdgeBuilder":
        """Sends the event to the target."""
        if target is None:
            raise TypeError("Target cannot be None")

        if isinstance(target, ProcessStepBuilder):
            target = ProcessFunctionTargetBuilder(
                step=target, parameter_name=kwargs.get("parameter_name"), function_name=kwargs.get("function_name")
            )

        self.target = target
        edge_builder = ProcessStepEdgeBuilder(source=self.source, event_id=self.event_id)
        edge_builder.target = self.target
        self.source.link_to(self.event_id, edge_builder)
        return ProcessEdgeBuilder(source=self.source, event_id=self.event_id)
