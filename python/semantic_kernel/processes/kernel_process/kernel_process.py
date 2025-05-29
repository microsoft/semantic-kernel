# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from pydantic import Field

from semantic_kernel.processes.kernel_process.kernel_process_edge import KernelProcessEdge
from semantic_kernel.processes.kernel_process.kernel_process_state import KernelProcessState
from semantic_kernel.processes.kernel_process.kernel_process_step_info import KernelProcessStepInfo
from semantic_kernel.processes.process_state_metadata_utils import kernel_process_to_process_state_metadata
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from semantic_kernel.processes.kernel_process.kernel_process_edge import KernelProcessEdge
    from semantic_kernel.processes.kernel_process.kernel_process_step_state_metadata import KernelProcessStateMetadata


@experimental
class KernelProcess(KernelProcessStepInfo):
    """A kernel process."""

    steps: list[KernelProcessStepInfo] = Field(default_factory=list)
    factories: dict[str, Callable] = Field(default_factory=dict)

    def __init__(
        self,
        state: KernelProcessState,
        steps: list[KernelProcessStepInfo],
        edges: dict[str, list["KernelProcessEdge"]] | None = None,
        factories: dict[str, Callable] | None = None,
    ):
        """Initialize the kernel process.

        Args:
            state: The state of the process.
            steps: The steps of the process.
            edges: The edges of the process. Defaults to None.
            factories: The factories of the process. This allows for the creation of
                steps that require complex dependencies that cannot be JSON serialized or deserialized.
        """
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

        if factories:
            args["factories"] = factories

        super().__init__(**args)

    def to_process_state_metadata(self) -> "KernelProcessStateMetadata":
        """Converts a kernel process to process state metadata."""
        return kernel_process_to_process_state_metadata(self)
