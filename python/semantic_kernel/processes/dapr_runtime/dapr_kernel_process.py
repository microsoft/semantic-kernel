# Copyright (c) Microsoft. All rights reserved.

from enum import Enum
from typing import TYPE_CHECKING

from semantic_kernel.exceptions.process_exceptions import ProcessInvalidConfigurationException
from semantic_kernel.processes.dapr_runtime.dapr_kernel_process_context import DaprKernelProcessContext
from semantic_kernel.processes.kernel_process.kernel_process_event import KernelProcessEvent
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess


@experimental
async def start(
    process: "KernelProcess",
    initial_event: KernelProcessEvent | str | Enum,
    process_id: str | None = None,
    max_supersteps: int | None = None,
    **kwargs,
) -> DaprKernelProcessContext:
    """Start the kernel process.

    Args:
        process: The kernel process to start.
        initial_event: The initial event to start the process with.
        process_id: The ID of the process. If None, a new ID will be generated.
        max_supersteps: The maximum number of supersteps. This is the total number of times process steps will run.
            Defaults to None, and thus the process will run its steps 100 times.
        **kwargs: Additional keyword arguments.
    """
    if process is None:
        raise ProcessInvalidConfigurationException("process cannot be None")
    if process.state is None:
        raise ProcessInvalidConfigurationException("process state cannot be empty")
    if initial_event is None:
        raise ProcessInvalidConfigurationException("initial_event cannot be None")

    initial_event_str: str | KernelProcessEvent = (
        initial_event.value if isinstance(initial_event, Enum) else initial_event
    )

    if isinstance(initial_event_str, str):
        initial_event_str = KernelProcessEvent(id=initial_event_str, data=kwargs.get("data"))

    if process_id is not None:
        process.state.id = process_id

    process_context = DaprKernelProcessContext(process=process, max_supersteps=max_supersteps)
    await process_context.start_with_event(initial_event_str)
    return process_context
