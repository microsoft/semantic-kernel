# Copyright (c) Microsoft. All rights reserved.

import json
from queue import Queue
from typing import TYPE_CHECKING

from dapr.actor import Actor

from semantic_kernel.processes.dapr_runtime.actors.actor_state_key import ActorStateKeys
from semantic_kernel.processes.dapr_runtime.message_buffer import MessageBuffer

if TYPE_CHECKING:
    from semantic_kernel.processes.process_message import ProcessMessage


class MessageBufferActor(Actor, MessageBuffer):
    """Represents a message buffer actor that follows the MessageBuffer abstract class."""

    queue: Queue = Queue()

    async def enqueue(self, message: "ProcessMessage") -> None:
        """Enqueues a message event into the buffer.

        Args:
            message: The message event to enqueue.
        """
        from semantic_kernel.processes.process_message import ProcessMessage

        message = ProcessMessage.model_validate(json.loads(message))
        self.queue.put(message)

        await self._state_manager.try_add_state(ActorStateKeys.MessageQueueState.value, self.queue)
        await self._state_manager.save_state()

    async def dequeue_all(self) -> "list[ProcessMessage]":
        """Dequeues all process events from the buffer.

        Returns:
            The dequeued message event.
        """
        items = []
        while not self.queue.empty():
            items.append(self.queue.get())

        await self._state_manager.try_add_state(ActorStateKeys.MessageQueueState.value, self.queue)
        await self._state_manager.save_state()

        return items

    async def on_activate(self) -> None:
        """Called when the actor is activated."""
        has_value, event_queue_state = await self._state_manager.try_get_state(ActorStateKeys.MessageQueueState.value)
        if has_value:
            self.queue = event_queue_state
        else:
            self.queue: Queue[ProcessMessage] = Queue()
