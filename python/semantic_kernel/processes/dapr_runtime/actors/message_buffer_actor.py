# Copyright (c) Microsoft. All rights reserved.

from queue import Queue
from typing import TYPE_CHECKING

from dapr.actor import Actor, ActorId
from dapr.actor.runtime.context import ActorRuntimeContext
from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.processes.dapr_runtime.actors.actor_state_key import ActorStateKeys
from semantic_kernel.processes.dapr_runtime.message_buffer import MessageBuffer

if TYPE_CHECKING:
    from semantic_kernel.processes.process_message import ProcessMessage


class MessageBufferActor(Actor, MessageBuffer, KernelBaseModel):
    """Represents a message buffer actor that follows the MessageBuffer abstract class."""

    queue: Queue = Field(default_factory=Queue)

    def __init__(self, ctx: ActorRuntimeContext, actor_id: ActorId):
        """Initializes a new instance of StepActor."""
        super().__init__(ctx, actor_id)

    async def enqueue(self, message: "ProcessMessage") -> None:
        """Enqueues a message event into the buffer.

        Args:
            message: The message event to enqueue.
        """
        self.queue.put(message)

        await self._state_manager.add_or_update_state(ActorStateKeys.MessageQueueState.value, self.queue)
        await self._state_manager.save_state()

    async def dequeue_all(self) -> "list[ProcessMessage]":
        """Dequeues all process events from the buffer.

        Returns:
            The dequeued message event.
        """
        items = []
        while not self.queue.empty():
            items.append(self.queue.get())

        await self._state_manager.add_or_update_state(ActorStateKeys.MessageQueueState.value, self.queue)
        await self._state_manager.save_state()

        return items

    async def on_activate(self) -> None:
        """Called when the actor is activated."""
        event_queue_state = await self._state_manager.get_state(ActorStateKeys.MessageQueueState.value, self.queue)
        if event_queue_state is not None:
            self.queue = event_queue_state
        else:
            self.queue: Queue[ProcessMessage] = Queue()
