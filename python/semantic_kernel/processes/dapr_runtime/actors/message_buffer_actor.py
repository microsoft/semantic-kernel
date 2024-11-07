# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from queue import Queue
from typing import TYPE_CHECKING, Any

from dapr.actor import Actor, ActorId
from dapr.actor.runtime.context import ActorRuntimeContext

from semantic_kernel.processes.dapr_runtime.actors.actor_state_key import ActorStateKeys
from semantic_kernel.processes.dapr_runtime.message_buffer_interface import MessageBufferInterface

if TYPE_CHECKING:
    from semantic_kernel.processes.process_message import ProcessMessage

logger: logging.Logger = logging.getLogger(__name__)


class MessageBufferActor(Actor, MessageBufferInterface):
    """Represents a message buffer actor that follows the MessageBuffer abstract class."""

    def __init__(self, ctx: ActorRuntimeContext, actor_id: ActorId):
        super().__init__(ctx, actor_id)
        self.queue: Queue[ProcessMessage] = Queue()

    async def enqueue(self, message: str) -> None:
        from semantic_kernel.processes.process_message import ProcessMessage

        try:
            message_obj = ProcessMessage.model_validate(json.loads(message))
            self.queue.put(message_obj)

            queue_list = [item.model_dump() for item in list(self.queue.queue)]
            await self._state_manager.try_add_state(ActorStateKeys.MessageQueueState.value, queue_list)
            await self._state_manager.save_state()
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error in enqueue: {error_message}")
            raise Exception(error_message)

    async def dequeue_all(self) -> list[dict[str, Any]]:
        try:
            items = []
            while not self.queue.empty():
                items.append(self.queue.get())

            queue_list = [item.model_dump() for item in list(self.queue.queue)]
            await self._state_manager.try_add_state(ActorStateKeys.MessageQueueState.value, queue_list)
            await self._state_manager.save_state()

            return [item.model_dump() for item in items]
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error in dequeue_all: {error_message}")
            raise Exception(error_message)

    async def _on_activate(self) -> None:
        from semantic_kernel.processes.process_message import ProcessMessage

        try:
            logger.debug(f"Activating actor with ID: {self.id.id}")

            has_value, queue_list = await self._state_manager.try_get_state(ActorStateKeys.MessageQueueState.value)
            if has_value and queue_list:
                self.queue = Queue()
                for item_dict in queue_list:
                    message_obj = ProcessMessage(**item_dict)
                    self.queue.put(message_obj)
            else:
                self.queue = Queue()
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error in _on_activate: {error_message}")
            raise Exception(error_message)
