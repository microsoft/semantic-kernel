# Copyright (c) Microsoft. All rights reserved.

from enum import Enum
from typing import TYPE_CHECKING

from semantic_kernel.exceptions.process_exceptions import ProcessInvalidConfigurationException
from semantic_kernel.processes.local_runtime.local_event import KernelProcessEvent
from semantic_kernel.processes.local_runtime.local_kernel_process_context import LocalKernelProcessContext
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from semantic_kernel.kernel import Kernel
    from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess


@experimental
async def start(
    process: "KernelProcess",
    kernel: "Kernel",
    initial_event: KernelProcessEvent | str | Enum,
    max_supersteps: int | None = None,
    **kwargs,
) -> LocalKernelProcessContext:
    """Start the kernel process.

    Args:
        process: The kernel process to start.
        kernel: The kernel instance.
        initial_event: The initial event to start the process with.
        max_supersteps: The maximum number of supersteps. This is the total number of times process steps will run.
                Defaults to None, and thus the process will run its steps 100 times.
        **kwargs: Additional keyword arguments.
    """
    if process is None:
        raise ProcessInvalidConfigurationException("process cannot be None")
    if process.state is None or not process.state.name:
        raise ProcessInvalidConfigurationException("process state name cannot be empty")
    if kernel is None:
        raise ProcessInvalidConfigurationException("kernel cannot be None")
    if initial_event is None:
        raise ProcessInvalidConfigurationException("initial_event cannot be None")

    initial_event_str: str | KernelProcessEvent = (
        initial_event.value if isinstance(initial_event, Enum) else initial_event
    )

    if isinstance(initial_event_str, str):
        initial_event_str = KernelProcessEvent(id=initial_event_str, data=kwargs.get("data"))

    process_context = LocalKernelProcessContext(process, kernel, max_supersteps)
    await process_context.start_with_event(initial_event_str)
    return process_context
