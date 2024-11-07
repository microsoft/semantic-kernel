# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from queue import Queue
from typing import List

from dapr.actor import Actor, ActorId
from dapr.actor.runtime.context import ActorRuntimeContext

from semantic_kernel.processes.dapr_runtime.actors.actor_state_key import ActorStateKeys
from semantic_kernel.processes.dapr_runtime.external_event_buffer_interface import ExternalEventBufferInterface
from semantic_kernel.processes.kernel_process.kernel_process_event import KernelProcessEvent

# Set up logging
logger = logging.getLogger(__name__)


class ExternalEventBufferActor(Actor, ExternalEventBufferInterface):
    """Represents a message buffer actor that follows the MessageBuffer abstract class."""

    def __init__(self, ctx: ActorRuntimeContext, actor_id: ActorId):
        """Initializes a new instance of ExternalEventBufferActor.

        Args:
            ctx: The actor runtime context.
            actor_id: The unique ID for the actor.
        """
        super().__init__(ctx, actor_id)
        self.queue: Queue[KernelProcessEvent] = Queue()

    async def enqueue(self, message: str) -> None:
        """Enqueues a message event into the buffer.

        Args:
            message: The message event to enqueue as a JSON string.

        Raises:
            Exception: If an error occurs during enqueue operation.
        """
        from semantic_kernel.processes.kernel_process.kernel_process_event import KernelProcessEvent

        try:
            # Deserialize and validate the incoming message
            message_obj = KernelProcessEvent.model_validate(json.loads(message))
            self.queue.put(message_obj)

            # Serialize the queue to a JSON string
            queue_list = [item.model_dump() for item in list(self.queue.queue)]
            queue_json = json.dumps(queue_list)

            # Save the serialized queue to Dapr state
            await self._state_manager.try_add_state(ActorStateKeys.ExternalEventQueueState.value, queue_json)
            await self._state_manager.save_state()
            logger.debug(f"Enqueued message and updated state for actor ID: {self.id.id}")
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error in enqueue: {error_message}")
            # Raise exception with JSON-serializable message
            raise Exception(error_message)

    async def dequeue_all(self) -> List[dict]:
        """Dequeues all process events from the buffer.

        Returns:
            A list of dictionaries representing the dequeued `KernelProcessEvent` messages.

        Raises:
            Exception: If an error occurs during dequeue operation.
        """
        try:
            items = []
            while not self.queue.empty():
                item = self.queue.get()
                items.append(item)

            # After dequeuing, update the state to reflect the empty queue
            queue_list = [item.model_dump() for item in list(self.queue.queue)]
            queue_json = json.dumps(queue_list)

            await self._state_manager.try_add_state(ActorStateKeys.ExternalEventQueueState.value, queue_json)
            await self._state_manager.save_state()
            logger.debug(f"Dequeued all messages and updated state for actor ID: {self.id.id}")

            # Return the dequeued items as a list of dictionaries
            return [item.model_dump() for item in items]
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error in dequeue_all: {error_message}")
            # Raise exception with JSON-serializable message
            raise Exception(error_message)

    async def _on_activate(self) -> None:
        """Called when the actor is activated to initialize state.

        Raises:
            Exception: If an error occurs during actor activation.
        """
        from semantic_kernel.processes.kernel_process.kernel_process_event import KernelProcessEvent

        try:
            logger.debug(f"Activating actor with ID: {self.id.id}")

            # Retrieve the stored queue from Dapr state
            state_exists, queue_json = await self._state_manager.try_get_state(
                ActorStateKeys.ExternalEventQueueState.value
            )
            if state_exists and queue_json:
                # Deserialize the JSON string back to a list of dictionaries
                queue_list = json.loads(queue_json)
                self.queue = Queue()
                for item_dict in queue_list:
                    message_obj = KernelProcessEvent(**item_dict)
                    self.queue.put(message_obj)
                logger.debug(f"Reconstructed queue from state for actor ID: {self.id.id}")
            else:
                self.queue = Queue()
                logger.debug(f"No existing state found. Initialized empty queue for actor ID: {self.id.id}")
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error in _on_activate: {error_message}")
            # Raise exception with JSON-serializable message
            raise Exception(error_message)
