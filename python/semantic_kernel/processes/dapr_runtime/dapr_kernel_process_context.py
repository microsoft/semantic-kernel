# Copyright (c) Microsoft. All rights reserved.

import uuid

from dapr.actor import ActorId, ActorProxy

from semantic_kernel.processes.dapr_runtime.dapr_process_info import DaprProcessInfo
from semantic_kernel.processes.dapr_runtime.process import Process
from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess
from semantic_kernel.processes.kernel_process.kernel_process_event import KernelProcessEvent


class DaprKernelProcessContext:
    """A Dapr kernel process context."""

    dapr_process: Process
    process: KernelProcess

    def __init__(self, process: KernelProcess):
        """Initialize a new instance of DaprKernelProcessContext."""
        if process.state.name is None:
            raise ValueError("Process state name must not be None")
        if process.state.id is None or process.state.id == "":
            process.state.id = str(uuid.uuid4().hex)

        self.process = process
        process_id = ActorId(process.state.id)
        self.dapr_process = ActorProxy.create(actor_interface=Process, actor_id=process_id, actor_type="ProcessActor")

    async def start_with_event(self, initial_event: KernelProcessEvent) -> None:
        """Starts the process with the provided initial event."""
        dapr_process = DaprProcessInfo.from_kernel_process(self.process)
        await self.dapr_process.initialize_process(dapr_process, None)
        await self.dapr_process.run_once(initial_event)

    async def send_event(self, event: KernelProcessEvent) -> None:
        """Sends an event to the process."""
        await self.dapr_process.send_message(event)

    async def stop(self) -> None:
        """Stops the process."""
        await self.dapr_process.stop()

    async def get_state(self) -> KernelProcess:
        """Retrieves the current state of the process."""
        dapr_process = await self.dapr_process.get_process_info()
        return dapr_process.to_kernel_process()
