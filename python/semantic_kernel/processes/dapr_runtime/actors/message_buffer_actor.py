# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from queue import Queue

from dapr.actor import Actor, ActorId
from dapr.actor.runtime.context import ActorRuntimeContext

from semantic_kernel.processes.dapr_runtime.actors.actor_state_key import ActorStateKeys
from semantic_kernel.processes.dapr_runtime.interfaces.message_buffer_interface import MessageBufferInterface
from semantic_kernel.utils.experimental_decorator import experimental_class

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class MessageBufferActor(Actor, MessageBufferInterface):
    """Represents a message buffer actor that follows the MessageBuffer abstract class."""

    def __init__(self, ctx: ActorRuntimeContext, actor_id: ActorId):
        """Initializes a new instance of MessageBufferActor."""
        super().__init__(ctx, actor_id)
        self.queue: Queue[str] = Queue()

    async def enqueue(self, message: str) -> None:
        """Enqueues a message event into the buffer and updates the state.

        Args:
            message (str): The message to enqueue.
        """
        try:
            self.queue.put(message)

            queue_list = list(self.queue.queue)
            await self._state_manager.try_add_state(ActorStateKeys.MessageQueueState.value, queue_list)
            await self._state_manager.save_state()

        except Exception as e:
            error_message = str(e)
            logger.error(f"Error in MessageBufferActor enqueue: {error_message}")
            raise Exception(error_message)

    async def dequeue_all(self) -> list[str]:
        """Dequeues all process events from the buffer and returns them as a list of strings."""
        try:
            items = []

            while not self.queue.empty():
                items.append(self.queue.get())

            await self._state_manager.try_add_state(ActorStateKeys.MessageQueueState.value, json.dumps([]))
            await self._state_manager.save_state()

            return items

        except Exception as e:
            error_message = str(e)
            logger.error(f"Error in MessageBufferActor dequeue_all: {error_message}")
            raise Exception(error_message)

    async def _on_activate(self) -> None:
        """Called when the actor is activated."""
        try:
            logger.info(f"Activating actor with ID: {self.id.id}")

            has_value, queue_list = await self._state_manager.try_get_state(ActorStateKeys.MessageQueueState.value)
            if has_value and queue_list:
                self.queue = Queue()
                for item_dict in queue_list:
                    self.queue.put(item_dict)
            else:
                self.queue = Queue()
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error in MessageBufferActor _on_activate: {error_message}")
            raise Exception(error_message)
