# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod

from dapr.actor import ActorInterface, actormethod

from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class EventBufferInterface(ActorInterface, ABC):
    """Abstract base class for an event buffer that follows the ActorInterface."""

    @abstractmethod
    @actormethod(name="enqueue")
    async def enqueue(self, step_event: str) -> None:
        """Enqueues a `ProcessEvent` step event into the buffer.

        Args:
            step_event: The step event to enqueue.
        """
        ...

    @abstractmethod
    @actormethod(name="dequeue_all")
    async def dequeue_all(self) -> list[str]:
        """Dequeues a step event from the buffer.

        Returns:
            The dequeued step event as a list of `ProcessEvent`.
        """
        ...
