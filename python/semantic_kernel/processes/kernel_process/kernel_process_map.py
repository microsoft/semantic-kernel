from semantic_kernel.processes.kernel_process.kernel_process_edge import KernelProcessEdge
from semantic_kernel.processes.kernel_process.kernel_process_map_state import KernelProcessMapState
from semantic_kernel.processes.kernel_process.kernel_process_step_info import KernelProcessStepInfo


class KernelProcessMap(KernelProcessStepInfo):
    """Information about a map step in a kernel process."""

    operation: KernelProcessStepInfo

    def __init__(
        self, state: KernelProcessMapState, operation: KernelProcessStepInfo, edges: dict[str, list[KernelProcessEdge]]
    ) -> None:
        """Initializes a new instance of the KernelProcessMap class."""
        super().__init__(KernelProcessMap, state, edges)
        self.operation = operation
