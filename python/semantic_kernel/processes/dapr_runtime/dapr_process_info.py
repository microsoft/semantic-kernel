# Copyright (c) Microsoft. All rights reserved.


from typing import Literal

from pydantic import Field

from semantic_kernel.processes.dapr_runtime.dapr_step_info import DaprStepInfo
from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess
from semantic_kernel.processes.kernel_process.kernel_process_state import KernelProcessState
from semantic_kernel.processes.kernel_process.kernel_process_step_info import KernelProcessStepInfo
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class DaprProcessInfo(DaprStepInfo):
    """A Dapr process info."""

    type: Literal["DaprProcessInfo"] = Field("DaprProcessInfo")  # type: ignore
    steps: list["DaprStepInfo | DaprProcessInfo"] = Field(default_factory=list)

    def to_kernel_process(self) -> KernelProcess:
        """Converts the Dapr process info to a kernel process."""
        if not isinstance(self.state, KernelProcessState):
            raise ValueError("State must be a kernel process state")

        steps: list[KernelProcessStepInfo] = []
        for step in self.steps:
            if isinstance(step, DaprProcessInfo):
                steps.append(step.to_kernel_process())
            else:
                steps.append(step.to_kernel_process_step_info())

        return KernelProcess(state=self.state, steps=steps, edges=self.edges)

    @classmethod
    def from_kernel_process(cls, kernel_process: KernelProcess) -> "DaprProcessInfo":
        """Creates a Dapr process info from a kernel process."""
        if kernel_process is None:
            raise ValueError("Kernel process must be provided")

        dapr_step_info = DaprStepInfo.from_kernel_step_info(kernel_process)
        dapr_steps: list[DaprProcessInfo | DaprStepInfo] = []

        for step in kernel_process.steps:
            if isinstance(step, KernelProcess):
                dapr_steps.append(DaprProcessInfo.from_kernel_process(step))
            else:
                dapr_steps.append(DaprStepInfo.from_kernel_step_info(step))

        return DaprProcessInfo(
            inner_step_python_type=dapr_step_info.inner_step_python_type,
            state=dapr_step_info.state,
            edges={key: list(value) for key, value in dapr_step_info.edges.items()},
            steps=dapr_steps,
        )
