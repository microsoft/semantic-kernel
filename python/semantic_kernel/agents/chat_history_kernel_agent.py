# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from abc import ABC, abstractmethod
from collections.abc import AsyncIterable

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override  # pragma: no cover

from semantic_kernel.agents.agent_channel import AgentChannel
from semantic_kernel.agents.chat_history_channel import ChatHistoryChannel
from semantic_kernel.agents.chat_history_handler import ChatHistoryHandler
from semantic_kernel.agents.kernel_agent import KernelAgent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.utils.experimental_decorator import experimental_class

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
class ChatHistoryKernelAgent(KernelAgent, ChatHistoryHandler, ABC):
    """A KernelAgent specialization bound to a ChatHistoryChannel."""

    def __init__(
        self,
        name: str | None = None,
        instructions: str | None = None,
        id: str | None = None,
        description: str | None = None,
    ) -> None:
        """Initialize the ChatHistoryKernelAgent.

        Args:
            name: The name of the agent.
            instructions: The instructions for the agent.
            id: The unique identifier for the agent.
            description: The description of the agent.
        """
        super().__init__(
            name=name,
            instructions=instructions,
            id=id,
            description=description,
        )

    @override
    def get_channel_keys(self) -> list[str]:
        """Get the channel keys.

        Returns:
            A list of channel keys.
        """
        return [ChatHistoryChannel.__name__]

    @override
    def create_channel(self) -> AgentChannel:  # type: ignore
        """Create a channel.

        Returns:
            An instance of AgentChannel.
        """
        return ChatHistoryChannel()

    @abstractmethod
    async def invoke(self, history: ChatHistory) -> AsyncIterable[ChatMessageContent]:
        """Invoke the chat history handler.

        Args:
            history: The chat history.

        Returns:
            An async iterable of ChatMessageContent.
        """
        ...

    @abstractmethod
    async def invoke_streaming(self, history: ChatHistory) -> AsyncIterable[StreamingChatMessageContent]:
        """Invoke the chat history handler in streaming mode.

        Args:
            history: The chat history.

        Returns:
            An async iterable of StreamingChatMessageContent.
        """
        ...
