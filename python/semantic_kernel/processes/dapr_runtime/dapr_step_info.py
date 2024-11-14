# Copyright (c) Microsoft. All rights reserved.

import importlib
from typing import Literal

from pydantic import Field

from semantic_kernel.exceptions.kernel_exceptions import KernelException
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.processes.kernel_process.kernel_process_edge import KernelProcessEdge
from semantic_kernel.processes.kernel_process.kernel_process_step_info import KernelProcessStepInfo
from semantic_kernel.processes.kernel_process.kernel_process_step_state import KernelProcessStepState
from semantic_kernel.processes.step_utils import get_fully_qualified_name
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class DaprStepInfo(KernelBaseModel):
    """A Dapr step info."""

    type: Literal["DaprStepInfo"] = Field("DaprStepInfo")
    inner_step_python_type: str
    state: KernelProcessStepState
    edges: dict[str, list[KernelProcessEdge]] = Field(default_factory=dict)

    def to_kernel_process_step_info(self) -> KernelProcessStepInfo:
        """Converts the Dapr step info to a kernel process step info."""
        inner_step_type = self._get_class_from_string(self.inner_step_python_type)
        if inner_step_type is None:
            raise KernelException(
                f"Unable to create inner step type from assembly qualified name `{self.inner_step_python_type}`"
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

    def _get_class_from_string(self, full_class_name: str):
        """Gets a class from a string."""
        module_name, class_name = full_class_name.rsplit(".", 1)
        module = importlib.import_module(module_name)
        return getattr(module, class_name)
