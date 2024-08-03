# Copyright (c) Microsoft. All rights reserved.

import sys
from collections.abc import AsyncIterable

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from abc import abstractmethod
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.agent_channel import AgentChannel
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.exceptions import ServiceInvalidTypeError
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.contents.chat_history import ChatHistory
    from semantic_kernel.contents.chat_message_content import ChatMessageContent
    from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent


@experimental_class
@runtime_checkable
class ChatHistoryAgentProtocol(Protocol):
    """Contract for an agent that utilizes a ChatHistoryChannel."""

    @abstractmethod
    def invoke(self, history: "ChatHistory") -> AsyncIterable["ChatMessageContent"]:
        """Invoke the chat history agent protocol."""
        ...

    @abstractmethod
    def invoke_stream(self, history: "ChatHistory") -> AsyncIterable["StreamingChatMessageContent"]:
        """Invoke the chat history agent protocol in streaming mode."""
        ...


@experimental_class
class ChatHistoryChannel(AgentChannel, ChatHistory):
    """An AgentChannel specialization for that acts upon a ChatHistoryHandler."""

    @override
    async def invoke(
        self,
        agent: Agent,
    ) -> AsyncIterable[ChatMessageContent]:
        """Perform a discrete incremental interaction between a single Agent and AgentChat.

        Args:
            agent: The agent to interact with.

        Returns:
            An async iterable of ChatMessageContent.
        """
        if not isinstance(agent, ChatHistoryAgentProtocol):
            id = getattr(agent, "id", "")
            raise ServiceInvalidTypeError(
                f"Invalid channel binding for agent with id: `{id}` with name: ({type(agent).__name__})"
            )

        async for message in agent.invoke(self):
            self.messages.append(message)
            yield message

    @override
    async def receive(
        self,
        history: list[ChatMessageContent],
    ) -> None:
        """Receive the conversation messages.

        Args:
            history: The history of messages in the conversation.
        """
        self.messages.extend(history)

    @override
    async def get_history(  # type: ignore
        self,
    ) -> AsyncIterable[ChatMessageContent]:
        """Retrieve the message history specific to this channel.

        Returns:
            An async iterable of ChatMessageContent.
        """
        for message in reversed(self.messages):
            yield message
