# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from semantic_kernel.processes.kernel_process.kernel_process_edge import KernelProcessEdge
from semantic_kernel.processes.local_runtime.local_message import LocalMessage
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class LocalMessageFactory:
    """Factory class to create LocalMessage instances."""

    @staticmethod
    def create_from_edge(edge: "KernelProcessEdge", data: Any | None = None) -> "LocalMessage":
        """Creates a new LocalMessage instance from a KernelProcessEdge and a data object."""
        target = edge.output_target
        parameter_value: dict[str, Any | None] = {}

        if target.parameter_name:
            parameter_value[target.parameter_name] = data

        return LocalMessage(
            source_id=edge.source_step_id,
            destination_id=target.step_id,
            function_name=target.function_name,
            values=parameter_value,
            target_event_id=target.target_event_id,
            target_event_data=data,
        )
