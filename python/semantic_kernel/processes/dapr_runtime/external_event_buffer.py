# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from dapr.actor import ActorInterface

if TYPE_CHECKING:
    from semantic_kernel.processes.kernel_process.kernel_process_event import KernelProcessEvent


class ExternalEventBuffer(ActorInterface, ABC):
    """Abstract base class for an external event buffer that follows the ActorInterface."""

    @abstractmethod
    async def enqueue(self, external_event: "KernelProcessEvent") -> None:
        """Enqueues an external event into the buffer.

        Args:
            external_event: The external event to enqueue.
        """
        pass

    @abstractmethod
    async def dequeue_all(self) -> "list[KernelProcessEvent]":
        """Dequeues all external events from the buffer.

        Returns:
            The dequeued external event.
        """
        pass
