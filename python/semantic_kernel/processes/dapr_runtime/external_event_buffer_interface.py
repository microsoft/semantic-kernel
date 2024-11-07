# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING

from dapr.actor import ActorInterface, actormethod

if TYPE_CHECKING:
    from semantic_kernel.processes.kernel_process.kernel_process_event import KernelProcessEvent


class ExternalEventBufferInterface(ActorInterface):
    """Abstract base class for an external event buffer that follows the ActorInterface."""

    @actormethod(name="enqueue")
    async def enqueue(self, external_event: str) -> None:
        """Enqueues an external event into the buffer.

        Args:
            external_event: The external event to enqueue.
        """
        pass

    @actormethod(name="dequeue_all")
    async def dequeue_all(self) -> "list[KernelProcessEvent]":
        """Dequeues all external events from the buffer.

        Returns:
            The dequeued external event.
        """
        pass
