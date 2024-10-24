# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING

from semantic_kernel.exceptions.process_exceptions import ProcessInvalidConfigurationException
from semantic_kernel.processes.local_runtime.local_event import KernelProcessEvent
from semantic_kernel.processes.local_runtime.local_kernel_process_context import LocalKernelProcessContext
from semantic_kernel.utils.experimental_decorator import experimental_function

if TYPE_CHECKING:
    from semantic_kernel.kernel import Kernel
    from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess


@experimental_function
async def start(
    process: "KernelProcess", kernel: "Kernel", initial_event: KernelProcessEvent | str, **kwargs
) -> LocalKernelProcessContext:
    """Start the kernel process."""
    if process is None:
        raise ProcessInvalidConfigurationException("process cannot be None")
    if process.state is None or not process.state.name:
        raise ProcessInvalidConfigurationException("process state name cannot be empty")
    if kernel is None:
        raise ProcessInvalidConfigurationException("kernel cannot be None")
    if initial_event is None:
        raise ProcessInvalidConfigurationException("initial_event cannot be None")

    if isinstance(initial_event, str):
        initial_event = KernelProcessEvent(id=initial_event, data=kwargs.get("data", None))

    process_context = LocalKernelProcessContext(process, kernel)
    await process_context.start_with_event(initial_event)
    return process_context
