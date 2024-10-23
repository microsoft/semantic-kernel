# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.exceptions.process_exceptions import ProcessEventUndefinedException
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.processes.kernel_process.kernel_process_message_channel import KernelProcessMessageChannel
from semantic_kernel.processes.local_runtime.local_event import KernelProcessEvent
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class KernelProcessStepContext(KernelBaseModel):
    """The context of a step in a kernel process."""

    step_message_channel: KernelProcessMessageChannel

    def __init__(self, channel: KernelProcessMessageChannel):
        """Initialize the step context."""
        super().__init__(step_message_channel=channel)

    def emit_event(self, process_event: "KernelProcessEvent") -> None:
        """Emit an event from the current step."""
        if process_event is None:
            raise ProcessEventUndefinedException("Process event cannot be None")
        self.step_message_channel.emit_event(process_event)
