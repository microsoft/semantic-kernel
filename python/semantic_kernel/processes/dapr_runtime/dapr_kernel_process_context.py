# Copyright (c) Microsoft. All rights reserved.

import uuid

from dapr.actor import ActorId, ActorProxy

from semantic_kernel.processes.dapr_runtime.actors.process_actor import ProcessActor
from semantic_kernel.processes.dapr_runtime.dapr_process_info import DaprProcessInfo
from semantic_kernel.processes.dapr_runtime.interfaces.process_interface import ProcessInterface
from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess
from semantic_kernel.processes.kernel_process.kernel_process_event import KernelProcessEvent
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class DaprKernelProcessContext:
    """A Dapr kernel process context."""

    dapr_process: ProcessInterface
    process: KernelProcess
    max_supersteps: int = 100

    def __init__(self, process: KernelProcess, max_supersteps: int | None = None) -> None:
        """Initialize a new instance of DaprKernelProcessContext.

        Args:
            process: The kernel process to start.
            max_supersteps: The maximum number of supersteps. This is the total number of times process steps will run.
                Defaults to None, and thus the process will run its steps 100 times.
        """
        if process.state.name is None:
            raise ValueError("Process state name must not be None")
        if process.state.id is None or process.state.id == "":
            process.state.id = str(uuid.uuid4().hex)

        if max_supersteps is not None:
            self.max_supersteps = max_supersteps

        self.process = process
        process_id = ActorId(process.state.id)
        self.dapr_process = ActorProxy.create(  # type: ignore
            actor_type=f"{ProcessActor.__name__}",
            actor_id=process_id,
            actor_interface=ProcessInterface,
        )

    async def start_with_event(self, initial_event: KernelProcessEvent) -> None:
        """Starts the process with the provided initial event."""
        dapr_process = DaprProcessInfo.from_kernel_process(self.process)
        dapr_process_dict = dapr_process.model_dump_json()

        payload = {
            "process_info": dapr_process_dict,
            "parent_process_id": None,
            "max_supersteps": self.max_supersteps,
        }

        await self.dapr_process.initialize_process(payload)
        initial_event_json = initial_event.model_dump_json()

        await self.dapr_process.run_once(initial_event_json)

    async def send_event(self, event: KernelProcessEvent) -> None:
        """Sends an event to the process."""
        await self.dapr_process.send_message(event)

    async def stop(self) -> None:
        """Stops the process."""
        await self.dapr_process.stop()

    async def get_state(self) -> KernelProcess:
        """Retrieves the current state of the process.

        Returns:
            The current state of the process.
        """
        raw_process_info = await self.dapr_process.get_process_info()
        dapr_process_info = DaprProcessInfo.model_validate(raw_process_info)
        return dapr_process_info.to_kernel_process()
