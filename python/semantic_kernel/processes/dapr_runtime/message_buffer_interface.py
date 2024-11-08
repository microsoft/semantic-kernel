# Copyright (c) Microsoft. All rights reserved.

from dapr.actor import ActorInterface, actormethod


class MessageBufferInterface(ActorInterface):
    """Abstract base class for a message event buffer that follows the ActorInterface."""

    @actormethod(name="enqueue")
    async def enqueue(self, message: str) -> None:
        """Enqueues a message event into the buffer.

        Args:
            message: The message event to enqueue.
        """
        pass

    @actormethod(name="dequeue_all")
    async def dequeue_all(self) -> list[str]:
        """Dequeues all process events from the buffer.

        Returns:
            The dequeued message event as a list of string
            representing a ProcessEvent.
        """
        pass
