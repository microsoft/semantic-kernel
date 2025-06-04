# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from semantic_kernel.processes.kernel_process.kernel_process_edge import KernelProcessEdge
from semantic_kernel.processes.process_message import ProcessMessage
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class ProcessMessageFactory:
    """Factory class for creating ProcessMessage instances."""

    @staticmethod
    def create_from_edge(edge: KernelProcessEdge, data: Any) -> ProcessMessage:
        """Creates a new ProcessMessage from a KernelProcessEdge."""
        target = edge.output_target
        parameter_value: dict[str, Any] = {}
        if target.parameter_name is not None:
            parameter_value[target.parameter_name] = data

        return ProcessMessage(
            source_id=edge.source_step_id,
            destination_id=target.step_id,
            function_name=target.function_name,
            values=parameter_value,
            target_event_id=target.target_event_id,
            target_event_data=data,
        )
