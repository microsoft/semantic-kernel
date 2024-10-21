# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING

from semantic_kernel.processes.kernel_process.kernel_process_edge import KernelProcessEdge
from semantic_kernel.processes.process_end_step import EndStep
from semantic_kernel.processes.process_function_target_builder import ProcessFunctionTargetBuilder
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.processes.process_step_builder import ProcessStepBuilder


@experimental_class
class ProcessStepEdgeBuilder:
    """A builder for a process step edge."""

    source: "ProcessStepBuilder"
    target: ProcessFunctionTargetBuilder | None = None
    event_id: str

    def __init__(self, source: "ProcessStepBuilder", event_id: str):
        """Initializes a new instance of ProcessStepEdgeBuilder."""
        self.source = source
        self.event_id = event_id

    def send_event_to(self, target: ProcessFunctionTargetBuilder) -> None:
        """Sends the event to the target."""
        if self.target is not None:
            raise Exception("An output target has already been set.")

        self.target = target
        self.source.link_to(self.event_id, self)

    def stop_process(self):
        """Stops the process."""
        if self.target is not None:
            raise Exception("An output target has already been set.")
        output_target = ProcessFunctionTargetBuilder(EndStep.get_instance())
        self.target = output_target
        self.source.link_to("END", self)

    def build(self) -> KernelProcessEdge:
        """Builds the KernelProcessEdge."""
        if not self.source.name:
            raise ValueError("Source step must have a valid name")
        if self.target is None:
            raise ValueError("Target must be provided")
        return KernelProcessEdge(source_step_id=self.source.id, output_target=self.target.build())
