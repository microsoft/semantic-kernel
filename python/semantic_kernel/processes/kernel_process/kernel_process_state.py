# Copyright (c) Microsoft. All rights reserved.

from typing import Literal

from pydantic import Field

from semantic_kernel.processes.kernel_process.kernel_process_step_state import KernelProcessStepState
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class KernelProcessState(KernelProcessStepState):
    """The state of a kernel process."""

    type: Literal["KernelProcessState"] = Field(default="KernelProcessState")  # type: ignore
