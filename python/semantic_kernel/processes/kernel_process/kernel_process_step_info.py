# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.processes.kernel_process.kernel_process_edge import KernelProcessEdge
from semantic_kernel.processes.kernel_process.kernel_process_step_state import KernelProcessStepState
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class KernelProcessStepInfo(KernelBaseModel):
    """Information about a step in a kernel process."""

    inner_step_type: type
    state: KernelProcessStepState
    output_edges: dict[str, list[KernelProcessEdge]]

    @property
    def edges(self) -> dict[str, list["KernelProcessEdge"]]:
        """The edges of the step."""
        return {k: v.copy() for k, v in self.output_edges.items()}
