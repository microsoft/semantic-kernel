# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING

from dapr.actor import ActorInterface, actormethod

if TYPE_CHECKING:
    from semantic_kernel.processes.process_event import ProcessEvent


class EventBufferInterface(ActorInterface):
    """Abstract base class for an event buffer that follows the ActorInterface."""

    @actormethod(name="enqueue")
    async def enqueue(self, step_event: str) -> None:
        """Enqueues a `ProcessEvent` step event into the buffer.

        Args:
            step_event: The step event to enqueue.
        """
        pass

    @actormethod(name="dequeue_all")
    async def dequeue_all(self) -> "list[ProcessEvent]":
        """Dequeues a step event from the buffer.

        Returns:
            The dequeued step event as a list of `ProcessEvent`.
        """
        pass
