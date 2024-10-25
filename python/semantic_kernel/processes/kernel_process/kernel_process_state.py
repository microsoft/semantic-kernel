# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.processes.kernel_process.kernel_process_step_state import KernelProcessStepState
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class KernelProcessState(KernelProcessStepState):
    """The state of a kernel process."""

    def __init__(self, name: str, id: str | None = None):
        """Initialize the state."""
        super().__init__(name=name, id=id)
