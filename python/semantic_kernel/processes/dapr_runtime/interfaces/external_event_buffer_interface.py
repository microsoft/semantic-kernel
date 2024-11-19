# Copyright (c) Microsoft. All rights reserved.


from abc import ABC, abstractmethod

from dapr.actor import ActorInterface, actormethod

from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class ExternalEventBufferInterface(ActorInterface, ABC):
    """Abstract base class for an external event buffer that follows the ActorInterface."""

    @abstractmethod
    @actormethod(name="enqueue")
    async def enqueue(self, external_event: str) -> None:
        """Enqueues an external event into the buffer.

        Args:
            external_event: The external event to enqueue.
        """
        ...

    @abstractmethod
    @actormethod(name="dequeue_all")
    async def dequeue_all(self) -> list[str]:
        """Dequeues all external events from the buffer as.

        The list is of string representations of KernelProcessEvent.

        Returns:
            The dequeued external event.
        """
        ...
