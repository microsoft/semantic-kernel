# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod

from dapr.actor import ActorInterface, actormethod

from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class MessageBufferInterface(ActorInterface, ABC):
    """Abstract base class for a message event buffer that follows the ActorInterface."""

    @abstractmethod
    @actormethod(name="enqueue")
    async def enqueue(self, message: str) -> None:
        """Enqueues a message event into the buffer.

        Args:
            message: The message event to enqueue.
        """
        ...

    @abstractmethod
    @actormethod(name="dequeue_all")
    async def dequeue_all(self) -> list[str]:
        """Dequeues all process events from the buffer.

        Returns:
            The dequeued message event as a list of string
            representing a ProcessEvent.
        """
        ...
