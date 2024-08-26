# Copyright (c) Microsoft. All rights reserved.

import sys
from collections import deque
from collections.abc import AsyncIterable

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from abc import abstractmethod
from typing import TYPE_CHECKING, Deque, Protocol, runtime_checkable

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.agent_channel import AgentChannel
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.exceptions import ServiceInvalidTypeError
from semantic_kernel.utils.experimental_decorator import experimental_class

if TYPE_CHECKING:
    from semantic_kernel.contents.chat_history import ChatHistory
    from semantic_kernel.contents.chat_message_content import ChatMessageContent
    from semantic_kernel.contents.streaming_chat_message_content import (
        StreamingChatMessageContent,
    )


@experimental_class
@runtime_checkable
class ChatHistoryAgentProtocol(Protocol):
    """Contract for an agent that utilizes a ChatHistoryChannel."""

    @abstractmethod
    def invoke(self, history: "ChatHistory") -> AsyncIterable["ChatMessageContent"]:
        """Invoke the chat history agent protocol."""
        ...

    @abstractmethod
    def invoke_stream(
        self, history: "ChatHistory"
    ) -> AsyncIterable["StreamingChatMessageContent"]:
        """Invoke the chat history agent protocol in streaming mode."""
        ...


@experimental_class
class ChatHistoryChannel(AgentChannel, ChatHistory):
    """An AgentChannel specialization for that acts upon a ChatHistoryHandler."""

    @override
    async def invoke(
        self,
        agent: Agent,
    ) -> AsyncIterable[tuple[bool, ChatMessageContent]]:
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

        message_count = len(self.messages)
        mutated_history = set()
        message_queue: Deque[ChatMessageContent] = deque()

        async for response_message in agent.invoke(self):
            # Capture all messages that have been included in the mutated history.
            for message_index in range(message_count, len(self.messages)):
                mutated_message = self.messages[message_index]
                mutated_history.add(mutated_message)
                message_queue.append(mutated_message)

            # Update the message count pointer to reflect the current history.
            message_count = len(self.messages)

            # Avoid duplicating any message included in the mutated history and also returned by the enumeration result.
            if response_message not in mutated_history:
                self.messages.append(response_message)
                message_queue.append(response_message)

            # Dequeue the next message to yield.
            yield_message = message_queue.popleft()
            yield (
                self._is_message_visible(
                    message=yield_message, message_queue_count=len(message_queue)
                ),
                yield_message,
            )

        # Dequeue any remaining messages to yield.
        while message_queue:
            yield_message = message_queue.popleft()
            yield (
                self._is_message_visible(
                    message=yield_message, message_queue_count=len(message_queue)
                ),
                yield_message,
            )

    def _is_message_visible(
        self, message: ChatMessageContent, message_queue_count: int
    ) -> bool:
        """Determine if a message is visible to the user."""
        return (
            not any(
                isinstance(item, (FunctionCallContent, FunctionResultContent))
                for item in message.items
            )
            or message_queue_count == 0
        )

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
