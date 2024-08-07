# Copyright (c) Microsoft. All rights reserved.


import asyncio
from collections.abc import Callable

from pydantic import Field

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.kernel_pydantic import KernelBaseModel


class BroadcastQueue(KernelBaseModel):
    """A queue for broadcasting messages to listeners."""

    queue: asyncio.Queue = Field(default_factory=asyncio.Queue)
    listeners: list[Callable] = Field(default_factory=list)

    def add_listener(self, listener: callable):
        """Add a listener to the broadcast queue."""
        self.listeners.append(listener)

    async def enqueue(self, messages: list[ChatMessageContent]):
        """Enqueue messages to the broadcast queue and notify listeners."""
        for message in messages:
            await self.queue.put(message)
            for listener in self.listeners:
                await listener(message)
