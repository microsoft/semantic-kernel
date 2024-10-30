# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from dapr.actor import ActorInterface

if TYPE_CHECKING:
    from semantic_kernel.processes.process_event import ProcessEvent


class EventBuffer(ActorInterface, ABC):
    """Abstract base class for an event buffer that follows the ActorInterface."""

    @abstractmethod
    async def enqueue(self, step_event: "ProcessEvent") -> None:
        """Enqueues a step event into the buffer.

        Args:
            step_event: The step event to enqueue.
        """
        pass

    @abstractmethod
    async def dequeue_all(self) -> "list[ProcessEvent]":
        """Dequeues a step event from the buffer.

        Returns:
            The dequeued step event.
        """
        pass
