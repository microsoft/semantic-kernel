# Copyright (c) Microsoft. All rights reserved.

import asyncio
import base64
import hashlib
import logging
import threading
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from pydantic import Field

from semantic_kernel.agents.agent_channel import AgentChannel
from semantic_kernel.agents.broadcast_queue import BroadcastQueue
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.kernel_pydantic import KernelBaseModel

if TYPE_CHECKING:
    from semantic_kernel.agents.agent import Agent

logger: logging.Logger = logging.getLogger(__name__)


class KeyEncoder:
    """A class for encoding keys."""

    @staticmethod
    def generate_hash(keys):
        """Generate a hash from a list of keys."""
        # Join the keys into a single string with ':' as the separator
        joined_keys = ":".join(keys)

        # Encode the joined string to bytes
        buffer = joined_keys.encode("utf-8")

        # Compute the SHA-256 hash
        sha256_hash = hashlib.sha256(buffer).digest()

        # Convert the hash to a base64-encoded string
        return base64.b64encode(sha256_hash).decode("utf-8")


class AgentChat(KernelBaseModel):
    """A base class chat interface for agents."""

    broadcast_queue: BroadcastQueue = Field(default_factory=BroadcastQueue)
    agent_channels: dict[str, AgentChannel] = Field(default_factory=dict)
    channel_map: dict[str, str] = Field(default_factory=dict)
    logger: logging.Logger = Field(default_factory=lambda: logging.getLogger("AgentChat"))
    history: ChatHistory = Field(default_factory=ChatHistory)

    _is_active: bool = False
    _lock: threading.Lock = threading.Lock()

    @property
    def is_active(self) -> bool:
        """Indicates whether the agent is currently active."""
        return self._is_active

    def set_activity_or_throw(self):
        """Set the activity signal or throw an exception if another agent is active."""
        with self._lock:
            if self._is_active:
                raise Exception("Unable to proceed while another agent is active.")
            self._is_active = True

    def clear_activity_signal(self):
        """Clear the activity signal."""
        with self._lock:
            self._is_active = False

    async def invoke(self) -> AsyncGenerator[ChatMessageContent, None]:
        """Invoke the agent asynchronously."""
        raise NotImplementedError("Subclasses should implement this method")

    async def get_messages_in_descending_order_async(self):
        """Get messages in descending order asynchronously."""
        for index in range(len(self.history.messages) - 1, -1, -1):
            yield self.history.messages[index]
            await asyncio.sleep(0)  # Yield control to the event loop

    async def get_chat_messages(self, agent: "Agent | None" = None) -> AsyncGenerator[ChatMessageContent, None]:
        """Get chat messages asynchronously."""
        self.set_activity_or_throw()

        logger.info("Getting chat messages")
        try:
            if agent is None:
                messages = self.get_messages_in_descending_order_async()
            else:
                # Handle agent-specific history retrieval here
                pass

            if messages is not None:
                async for message in messages:
                    yield message
            messages = reversed(self.history.messages) if agent is None else self.agent_channels.get(agent.id).messages
            if messages:
                for message in messages:
                    yield message
        finally:
            self.clear_activity_signal()

    def get_agent_hash(self, agent: Agent):
        """Get the hash of an agent."""
        if agent not in self.channel_map:
            hash_value = KeyEncoder.generate_hash(agent.get_channel_keys())
            # Ok if already present: same agent always produces the same hash
            self.channel_map[agent] = hash_value

        return self.channel_map[agent]

    async def add_chat_messages(self, messages: list[ChatMessageContent]):
        """Add chat messages."""
        self.set_activity_or_throw()
        self.logger.info("Adding messages")
        try:
            self.history.messages.extend(messages)
            await asyncio.create_task(self.broadcast_queue.enqueue(messages))
        finally:
            self.clear_activity_signal()

    async def invoke_agent(self, agent: Agent) -> AsyncGenerator[ChatMessageContent, None]:
        """Invoke an agent asynchronously."""
        self.set_activity_or_throw()
        self.logger.info(f"Invoking agent {agent.name}")
        try:
            channel = self.agent_channels.get(agent.id)
            if channel is None:
                channel = await self.create_channel(agent)
                self.agent_channels[agent.id] = channel

            async for message in self.process_agent_interaction(agent, channel):
                yield message
        finally:
            self.clear_activity_signal()

    async def create_channel(self, agent: Agent) -> AgentChannel:
        """Create a channel for an agent."""
        self.logger.info(f"Creating channel for agent {agent.name}")
        return AgentChannel(id=agent.id)

    async def process_agent_interaction(
        self, agent: Agent, channel: AgentChannel
    ) -> AsyncGenerator[ChatMessageContent, None]:
        """Process an agent interaction asynchronously."""
        async for message in channel.invoke(agent):
            self.history.messages.append(message)
            yield message
