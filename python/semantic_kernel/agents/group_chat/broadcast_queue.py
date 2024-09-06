# Copyright (c) Microsoft. All rights reserved.


import asyncio
from collections import deque
from dataclasses import dataclass, field

from pydantic import Field, SkipValidation, ValidationError, model_validator

from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class QueueReference(KernelBaseModel):
    """Utility class to associate a queue with its specific lock."""

    queue: deque = Field(default_factory=deque)
    queue_lock: SkipValidation[asyncio.Lock] = Field(default_factory=asyncio.Lock, exclude=True)
    receive_task: SkipValidation[asyncio.Task | None] = None
    receive_failure: Exception | None = None

    @property
    def is_empty(self):
        """Check if the queue is empty."""
        return len(self.queue) == 0

    @model_validator(mode="before")
    def validate_receive_task(cls, values):
        """Validate the receive task."""
        receive_task = values.get("receive_task")
        if receive_task is not None and not isinstance(receive_task, asyncio.Task):
            raise ValidationError("receive_task must be an instance of asyncio.Task or None")
        return values


@experimental_class
@dataclass
class ChannelReference:
    """Tracks a channel along with its hashed key."""

    hash: str
    channel: AgentChannel = field(default_factory=AgentChannel)


@experimental_class
class BroadcastQueue(KernelBaseModel):
    """A queue for broadcasting messages to listeners."""

    queues: dict[str, QueueReference] = Field(default_factory=dict)
    block_duration: float = 0.1

    async def enqueue(self, channel_refs: list[ChannelReference], messages: list[ChatMessageContent]) -> None:
        """Enqueue a set of messages for a given channel.

        Args:
            channel_refs: The channel references.
            messages: The messages to broadcast.
        """
        for channel_ref in channel_refs:
            if channel_ref.hash not in self.queues:
                self.queues[channel_ref.hash] = QueueReference()

            queue_ref = self.queues[channel_ref.hash]

            async with queue_ref.queue_lock:
                queue_ref.queue.append(messages)

                if not queue_ref.receive_task or queue_ref.receive_task.done():
                    queue_ref.receive_task = asyncio.create_task(self.receive(channel_ref, queue_ref))

    async def ensure_synchronized(self, channel_ref: ChannelReference) -> None:
        """Blocks until a channel-queue is not in a receive state to ensure that channel history is complete.

        Args:
            channel_ref: The channel reference.
        """
        if channel_ref.hash not in self.queues:
            return

        queue_ref = self.queues[channel_ref.hash]

        while True:
            async with queue_ref.queue_lock:
                is_empty = queue_ref.is_empty

                if queue_ref.receive_failure is not None:
                    failure = queue_ref.receive_failure
                    queue_ref.receive_failure = None
                    raise Exception(
                        f"Unexpected failure broadcasting to channel: {type(channel_ref.channel)}, failure: {failure}"
                    ) from failure

                if not is_empty and (not queue_ref.receive_task or queue_ref.receive_task.done()):
                    queue_ref.receive_task = asyncio.create_task(self.receive(channel_ref, queue_ref))

            if is_empty:
                break

            await asyncio.sleep(self.block_duration)

    async def receive(self, channel_ref: ChannelReference, queue_ref: QueueReference) -> None:
        """Processes the specified queue with the provided channel, until the queue is empty.

        Args:
            channel_ref: The channel reference.
            queue_ref: The queue reference.
        """
        while True:
            async with queue_ref.queue_lock:
                if queue_ref.is_empty:
                    break

                messages = queue_ref.queue[0]
            try:
                await channel_ref.channel.receive(messages)
            except Exception as e:
                queue_ref.receive_failure = e

            async with queue_ref.queue_lock:
                if not queue_ref.is_empty:
                    queue_ref.queue.popleft()

                if queue_ref.receive_failure is not None or queue_ref.is_empty:
                    break
