# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import threading
from collections.abc import AsyncIterable

from pydantic import Field, PrivateAttr

from semantic_kernel.agents import Agent
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.agents.group_chat.agent_chat_utils import KeyEncoder
from semantic_kernel.agents.group_chat.broadcast_queue import BroadcastQueue, ChannelReference
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentChatException
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.feature_stage_decorator import experimental

logger: logging.Logger = logging.getLogger(__name__)


@experimental
class AgentChat(KernelBaseModel):
    """A base class chat interface for agents."""

    broadcast_queue: BroadcastQueue = Field(default_factory=BroadcastQueue)
    agent_channels: dict[str, AgentChannel] = Field(default_factory=dict)
    channel_map: dict[Agent, str] = Field(default_factory=dict)
    history: ChatHistory = Field(default_factory=ChatHistory)

    _lock: threading.Lock = PrivateAttr(default_factory=threading.Lock)
    _is_active: bool = False

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

    def invoke(self, agent: Agent | None = None, is_joining: bool = True) -> AsyncIterable[ChatMessageContent]:
        """Invoke the agent asynchronously."""
        raise NotImplementedError("Subclasses should implement this method")

    async def get_messages_in_descending_order(self) -> AsyncIterable[ChatMessageContent]:
        """Get messages in descending order asynchronously."""
        for index in range(len(self.history.messages) - 1, -1, -1):
            yield self.history.messages[index]
            await asyncio.sleep(0)  # Yield control to the event loop

    async def get_chat_messages(self, agent: "Agent | None" = None) -> AsyncIterable[ChatMessageContent]:
        """Get chat messages asynchronously."""
        self.set_activity_or_throw()

        logger.info("Getting chat messages")

        messages: AsyncIterable[ChatMessageContent] | None = None
        try:
            if agent is None:
                messages = self.get_messages_in_descending_order()
            else:
                channel_key = self._get_agent_hash(agent)
                channel = await self._synchronize_channel(channel_key)
                if channel is not None:
                    messages = channel.get_history()
            if messages is not None:
                async for message in messages:
                    yield message
        finally:
            self.clear_activity_signal()

    async def _synchronize_channel(self, channel_key: str) -> AgentChannel | None:
        """Synchronize a channel."""
        channel = self.agent_channels.get(channel_key, None)
        if channel:
            await self.broadcast_queue.ensure_synchronized(ChannelReference(channel=channel, hash=channel_key))
        return channel

    def _get_agent_hash(self, agent: Agent):
        """Get the hash of an agent."""
        hash_value = self.channel_map.get(agent, None)
        if hash_value is None:
            hash_value = KeyEncoder.generate_hash(agent.get_channel_keys())
            self.channel_map[agent] = hash_value

        return hash_value

    async def add_chat_message(self, message: str | ChatMessageContent) -> None:
        """Add a chat message."""
        if isinstance(message, str):
            message = ChatMessageContent(role=AuthorRole.USER, content=message)

        await self.add_chat_messages([message])

    async def add_chat_messages(self, messages: list[ChatMessageContent]) -> None:
        """Add chat messages."""
        self.set_activity_or_throw()

        for message in messages:
            if message.role == AuthorRole.SYSTEM:
                error_message = "System messages cannot be added to the chat history."
                logger.error(error_message)
                raise AgentChatException(error_message)

        logger.info(f"Adding `{len(messages)}` agent chat messages")

        try:
            self.history.messages.extend(messages)

            # Broadcast message to other channels (in parallel)
            # Note: Able to queue messages without synchronizing channels.
            channel_refs = [ChannelReference(channel=channel, hash=key) for key, channel in self.agent_channels.items()]
            await self.broadcast_queue.enqueue(channel_refs, messages)
        finally:
            self.clear_activity_signal()

    async def _get_or_create_channel(self, agent: Agent) -> AgentChannel:
        """Get or create a channel."""
        channel_key = self._get_agent_hash(agent)
        channel = await self._synchronize_channel(channel_key)
        if channel is None:
            channel = await agent.create_channel()
            self.agent_channels[channel_key] = channel

            if len(self.history.messages) > 0:
                await channel.receive(self.history.messages)
        return channel

    async def invoke_agent(self, agent: Agent) -> AsyncIterable[ChatMessageContent]:
        """Invoke an agent asynchronously."""
        self.set_activity_or_throw()
        logger.info(f"Invoking agent {agent.name}")
        try:
            channel: AgentChannel = await self._get_or_create_channel(agent)
            messages: list[ChatMessageContent] = []

            async for is_visible, message in channel.invoke(agent):
                messages.append(message)
                self.history.messages.append(message)
                if is_visible:
                    yield message

            # Broadcast message to other channels (in parallel)
            # Note: Able to queue messages without synchronizing channels.
            channel_refs = [
                ChannelReference(channel=ch, hash=key) for key, ch in self.agent_channels.items() if ch != channel
            ]
            await self.broadcast_queue.enqueue(channel_refs, messages)
        finally:
            self.clear_activity_signal()

    async def invoke_agent_stream(self, agent: Agent) -> AsyncIterable[ChatMessageContent]:
        """Invoke an agent stream asynchronously."""
        self.set_activity_or_throw()
        logger.info(f"Invoking agent {agent.name}")
        try:
            channel: AgentChannel = await self._get_or_create_channel(agent)
            messages: list[ChatMessageContent] = []

            async for message in channel.invoke_stream(agent, messages):
                yield message

            for message in messages:
                self.history.messages.append(message)

            # Broadcast message to other channels (in parallel)
            # Note: Able to queue messages without synchronizing channels.
            channel_refs = [
                ChannelReference(channel=ch, hash=key) for key, ch in self.agent_channels.items() if ch != channel
            ]
            await self.broadcast_queue.enqueue(channel_refs, messages)
        finally:
            self.clear_activity_signal()

    async def reset(self) -> None:
        """Reset the agent chat."""
        self.set_activity_or_throw()

        try:
            await asyncio.gather(*(channel.reset() for channel in self.agent_channels.values()))
            self.agent_channels.clear()
            self.channel_map.clear()
            self.history.messages.clear()
        finally:
            self.clear_activity_signal()
