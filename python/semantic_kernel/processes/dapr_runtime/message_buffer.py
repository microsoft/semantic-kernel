# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING

from dapr.actor import ActorInterface, actormethod

if TYPE_CHECKING:
    from semantic_kernel.processes.process_event import ProcessEvent


class MessageBuffer(ActorInterface):
    """Abstract base class for a message event buffer that follows the ActorInterface."""

    @actormethod
    async def enqueue(self, message: "ProcessEvent") -> None:
        """Enqueues a message event into the buffer.

        Args:
            message: The message event to enqueue.
        """
        pass

    @actormethod
    async def dequeue_all(self) -> "list[ProcessEvent]":
        """Dequeues all process events from the buffer.

        Returns:
            The dequeued message event.
        """
        pass
