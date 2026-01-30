# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Sequence
from typing import Literal

from pydantic import Field

from semantic_kernel.exceptions.kernel_exceptions import KernelException
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.processes.kernel_process.kernel_process_edge import KernelProcessEdge
from semantic_kernel.processes.kernel_process.kernel_process_state import KernelProcessState
from semantic_kernel.processes.kernel_process.kernel_process_step_info import KernelProcessStepInfo
from semantic_kernel.processes.kernel_process.kernel_process_step_state import KernelProcessStepState
from semantic_kernel.processes.step_utils import get_fully_qualified_name, get_step_class_from_qualified_name
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class DaprStepInfo(KernelBaseModel):
    """A Dapr step info."""

    type: Literal["DaprStepInfo"] = "DaprStepInfo"
    inner_step_python_type: str
    state: KernelProcessState | KernelProcessStepState
    edges: dict[str, list[KernelProcessEdge]] = Field(default_factory=dict)

    def to_kernel_process_step_info(
        self, allowed_module_prefixes: Sequence[str] | None = None
    ) -> KernelProcessStepInfo:
        """Converts the Dapr step info to a kernel process step info.

        Args:
            allowed_module_prefixes: Optional list of module prefixes that are allowed
                for step class loading. If provided, step classes must come from modules
                starting with one of these prefixes.
        """
        inner_step_type = get_step_class_from_qualified_name(
            self.inner_step_python_type,
            allowed_module_prefixes=allowed_module_prefixes,
        )
        return KernelProcessStepInfo(inner_step_type=inner_step_type, state=self.state, output_edges=self.edges)

    @classmethod
    def from_kernel_step_info(cls, kernel_step_info: KernelProcessStepInfo) -> "DaprStepInfo":
        """Creates a Dapr step info from a kernel step info."""
        if kernel_step_info is None:
            raise KernelException("Kernel step info must be provided")

        inner_step_type = get_fully_qualified_name(kernel_step_info.inner_step_type)

        return DaprStepInfo(
            inner_step_python_type=inner_step_type,
            state=kernel_step_info.state,
            edges={key: list(value) for key, value in kernel_step_info.edges.items()},
        )
