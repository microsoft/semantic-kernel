# Copyright (c) Microsoft. All rights reserved.

import json
from queue import Queue
from typing import TYPE_CHECKING

from dapr.actor import Actor

from semantic_kernel.processes.dapr_runtime.actors.actor_state_key import ActorStateKeys
from semantic_kernel.processes.dapr_runtime.message_buffer_interface import MessageBufferInterface

if TYPE_CHECKING:
    from semantic_kernel.processes.process_event import ProcessEvent


class EventBufferActor(Actor, MessageBufferInterface):
    """Represents a message buffer actor that follows the MessageBuffer abstract class."""

    queue: Queue = Queue()

    # async def enqueue(self, message: "ProcessEvent") -> None:
    #     """Enqueues a message event into the buffer.

    #     Args:
    #         message: The message event to enqueue.
    #     """
    #     from semantic_kernel.processes.process_event import ProcessEvent

    #     message = ProcessEvent.model_validate(json.loads(message))

    #     self.queue.put(message)

    #     await self._state_manager.try_add_state(ActorStateKeys.EventQueueState.value, self.queue)
    #     await self._state_manager.save_state()

    # async def dequeue_all(self) -> "list[ProcessEvent]":
    #     """Dequeues all process events from the buffer.

    #     Returns:
    #         The dequeued message event.
    #     """
    #     items = []
    #     while not self.queue.empty():
    #         items.append(self.queue.get())

    #     await self._state_manager.try_add_state(ActorStateKeys.EventQueueState.value, self.queue)
    #     await self._state_manager.save_state()

    #     return items

    # async def on_activate(self) -> None:
    #     """Called when the actor is activated."""
    #     has_value, event_queue_state = await self._state_manager.try_get_state(ActorStateKeys.EventQueueState.value)
    #     if has_value:
    #         self.queue = event_queue_state
    #     else:
    #         self.queue: Queue["ProcessEvent"] = Queue()

    async def enqueue(self, message: "ProcessEvent") -> None:
        # Validate and deserialize the message
        message = ProcessEvent.model_validate(json.loads(message))
        self.queue.put(message)

        # Convert queue to a list of serializable dictionaries
        queue_items = list(self.queue.queue)
        queue_dicts = [item.model_dump() for item in queue_items]

        # Save the serializable queue to Dapr state
        await self._state_manager.try_add_state(ActorStateKeys.EventQueueState.value, queue_dicts)
        await self._state_manager.save_state()

    async def dequeue_all(self) -> "list[ProcessEvent]":
        items = []
        while not self.queue.empty():
            items.append(self.queue.get())

        # Save the updated queue state
        queue_items = list(self.queue.queue)
        queue_dicts = [item.model_dump() for item in queue_items]
        await self._state_manager.try_add_state(ActorStateKeys.EventQueueState.value, queue_dicts)
        await self._state_manager.save_state()

        # Return a list of serializable dictionaries
        return [item.model_dump() for item in items]

    async def _on_activate(self) -> None:
        has_value, event_queue_state = await self._state_manager.try_get_state(ActorStateKeys.EventQueueState.value)
        if has_value:
            queue_dicts = event_queue_state
            self.queue = Queue()
            for item_dict in queue_dicts:
                message = ProcessEvent(**item_dict)
                self.queue.put(message)
        else:
            self.queue = Queue()
