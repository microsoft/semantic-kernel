# Copyright (c) Microsoft. All rights reserved.

from enum import Enum
from typing import TYPE_CHECKING

from semantic_kernel.exceptions.process_exceptions import ProcessInvalidConfigurationException
from semantic_kernel.processes.dapr_runtime.dapr_kernel_process_context import DaprKernelProcessContext
from semantic_kernel.processes.kernel_process.kernel_process_event import KernelProcessEvent
from semantic_kernel.utils.experimental_decorator import experimental_function

if TYPE_CHECKING:
    from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess


@experimental_function
async def start(
    process: "KernelProcess",
    initial_event: KernelProcessEvent | str | Enum,
    process_id: str | None = None,
    **kwargs,
) -> DaprKernelProcessContext:
    """Start the kernel process."""
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

    process_context = DaprKernelProcessContext(process=process)
    await process_context.start_with_event(initial_event_str)
    return process_context
