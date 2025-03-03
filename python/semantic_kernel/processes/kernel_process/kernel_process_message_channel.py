# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod

from semantic_kernel.processes.local_runtime.local_event import KernelProcessEvent
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class KernelProcessMessageChannel(ABC):
    """Abstract base class for emitting events from a step."""

    @abstractmethod
    async def emit_event(self, process_event: "KernelProcessEvent") -> None:
        """Emits the specified event from the step."""
        pass
