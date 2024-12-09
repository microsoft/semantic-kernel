from semantic_kernel.processes.kernel_process.kernel_process_step_state import KernelProcessStepState


class KernelProcessMapState(KernelProcessStepState):
    """The state of a map step in a kernel process."""

    def __init__(self, name: str, version: str, id: str) -> None:
        """Initializes a new instance of the KernelProcessMapState class."""
        super().__init__(name, version, id)
