# Copyright (c) Microsoft. All rights reserved.

import json
from queue import Queue
from typing import TYPE_CHECKING

from dapr.actor import Actor

from semantic_kernel.processes.dapr_runtime.actors.actor_state_key import ActorStateKeys
from semantic_kernel.processes.dapr_runtime.external_event_buffer import ExternalEventBuffer
from semantic_kernel.processes.kernel_process.kernel_process_event import KernelProcessEvent

if TYPE_CHECKING:
    pass


class ExternalEventBufferActor(Actor, ExternalEventBuffer):
    """Represents a message buffer actor that follows the MessageBuffer abstract class."""

    queue: Queue = Queue()

    async def enqueue(self, message: str) -> None:
        """Enqueues a message event into the buffer.

        Args:
            message: The message event to enqueue.
        """
        # Perform validation that we have the correct incoming message
        message = KernelProcessEvent.model_validate(json.loads(message))
        self.queue.put(message)

        try:
            # Convert each item in the queue to a dictionary for serialization
            queue_list = [item.model_dump() for item in self.queue.queue]
            queue_dict = json.dumps(queue_list)

            await self._state_manager.try_add_state(ActorStateKeys.ExternalEventQueueState.value, queue_dict)
            await self._state_manager.save_state()
        except Exception as e:
            print(e)
            raise e

    async def dequeue_all(self) -> "list[KernelProcessEvent]":
        """Dequeues all process events from the buffer.

        Returns:
            The dequeued message event.
        """
        items = []
        while not self.queue.empty():
            items.append(self.queue.get())

        await self._state_manager.try_add_state(ActorStateKeys.ExternalEventQueueState.value, self.queue)
        await self._state_manager.save_state()

        return items

    async def _on_activate(self) -> None:
        """Called when the actor is activated."""
        state_exists, event_queue_state = await self._state_manager.try_get_state(
            ActorStateKeys.ExternalEventQueueState.value
        )
        if state_exists:
            self.queue = event_queue_state
        else:
            self.queue: Queue[KernelProcessEvent] = Queue()
