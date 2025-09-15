# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING

from semantic_kernel.kernel import Kernel
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.processes.local_runtime.local_process import LocalProcess
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess
    from semantic_kernel.processes.local_runtime.local_event import KernelProcessEvent


@experimental
class LocalKernelProcessContext(KernelBaseModel):
    """A local kernel process context."""

    local_process: LocalProcess

    def __init__(self, process: "KernelProcess", kernel: "Kernel", max_supersteps: int | None = None) -> None:
        """Initializes the local kernel process context.

        Args:
            process: The kernel process to start.
            kernel: The kernel instance.
            max_supersteps: The maximum number of supersteps. This is the total number of times process steps will run.
                Defaults to None.
        """
        from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess  # noqa: F401

        LocalProcess.model_rebuild()

        if not process or not process.state or not process.state.name.strip():
            raise ValueError("Process and process state must be provided and have a valid name")
        if not kernel:
            raise ValueError("Kernel must be provided")

        local_process = LocalProcess(
            process=process,
            kernel=kernel,
            parent_process_id=None,
            factories=process.factories,
            max_supersteps=max_supersteps,
        )

        super().__init__(local_process=local_process)  # type: ignore

    async def start_with_event(self, initial_event: "KernelProcessEvent") -> None:
        """Starts the local process with an initial event."""
        await self.local_process.run_once(initial_event)

    async def send_event(self, process_event: "KernelProcessEvent") -> None:
        """Sends an event to the process."""
        await self.local_process.send_message(process_event)

    async def stop(self) -> None:
        """Stops the local process."""
        await self.local_process.stop()

    async def get_state(self) -> "KernelProcess":
        """Gets the current state of the process."""
        return await self.local_process.get_process_info()

    async def __aenter__(self):
        """Enters the async context (used for resource management)."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exits the async context and disposes of resources."""
        await self.dispose()

    async def dispose(self) -> None:
        """Disposes of the resources used by the process."""
        if self.local_process:
            self.local_process.dispose()
