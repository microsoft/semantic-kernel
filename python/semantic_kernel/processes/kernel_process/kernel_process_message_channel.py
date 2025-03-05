# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod

from semantic_kernel.processes.local_runtime.local_event import KernelProcessEvent
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class KernelProcessMessageChannel(ABC):
    """Abstract base class for emitting events from a step."""

    @abstractmethod
    async def emit_event(self, process_event: "KernelProcessEvent") -> None:
        """Emits the specified event from the step."""
        pass
