# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING, Any

from pydantic import Field

from semantic_kernel.processes.kernel_process.kernel_process_edge import KernelProcessEdge
from semantic_kernel.processes.kernel_process.kernel_process_state import KernelProcessState
from semantic_kernel.processes.kernel_process.kernel_process_step_info import KernelProcessStepInfo
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.processes.kernel_process.kernel_process_edge import KernelProcessEdge


@experimental_class
class KernelProcess(KernelProcessStepInfo):
    """A kernel process."""

    steps: list[KernelProcessStepInfo] = Field(default_factory=list)

    def __init__(
        self,
        state: KernelProcessState,
        steps: list[KernelProcessStepInfo],
        edges: dict[str, list["KernelProcessEdge"]] | None = None,
    ):
        """Initialize the kernel process."""
        if not state:
            raise ValueError("state cannot be None")
        if not steps:
            raise ValueError("steps cannot be None")
        if not state.name:
            raise ValueError("state.Name cannot be None")

        process_steps = []
        process_steps.extend(steps)

        args: dict[str, Any] = {
            "steps": process_steps,
            "inner_step_type": KernelProcess,
            "state": state,
            "output_edges": edges or {},
        }

        super().__init__(**args)
