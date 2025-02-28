# Copyright (c) Microsoft. All rights reserved.

import sys
from collections import deque
from collections.abc import AsyncIterable
from copy import deepcopy

from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.text_content import TextContent

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from typing import TYPE_CHECKING, Any, ClassVar, Deque

from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.utils.feature_stage_decorator import experimental

if TYPE_CHECKING:
    from semantic_kernel.agents.agent import Agent
    from semantic_kernel.contents.chat_history import ChatHistory
    from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent


@experimental
class ChatHistoryChannel(AgentChannel, ChatHistory):
    """An AgentChannel specialization for that acts upon a ChatHistoryHandler."""

    ALLOWED_CONTENT_TYPES: ClassVar[tuple[type, ...]] = (
        ImageContent,
        FunctionCallContent,
        FunctionResultContent,
        StreamingTextContent,
        TextContent,
    )

    @override
    async def invoke(
        self,
        agent: "Agent",
        **kwargs: Any,
    ) -> AsyncIterable[tuple[bool, ChatMessageContent]]:
        """Perform a discrete incremental interaction between a single Agent and AgentChat.

        Args:
            agent: The agent to interact with.
            kwargs: The keyword arguments.

        Returns:
            An async iterable of ChatMessageContent.
        """
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
                self._is_message_visible(message=yield_message, message_queue_count=len(message_queue)),
                yield_message,
            )

        # Dequeue any remaining messages to yield.
        while message_queue:
            yield_message = message_queue.popleft()
            yield (
                self._is_message_visible(message=yield_message, message_queue_count=len(message_queue)),
                yield_message,
            )

    @override
    async def invoke_stream(
        self, agent: "Agent", messages: list[ChatMessageContent], **kwargs: Any
    ) -> AsyncIterable["StreamingChatMessageContent"]:
        """Perform a discrete incremental stream interaction between a single Agent and AgentChat.

        Args:
            agent: The agent to interact with.
            messages: The history of messages in the conversation.
            kwargs: The keyword arguments

        Returns:
            An async iterable of ChatMessageContent.
        """
        message_count = len(self.messages)

        async for response_message in agent.invoke_stream(self):
            if response_message.content:
                yield response_message

        for message_index in range(message_count, len(self.messages)):
            messages.append(self.messages[message_index])

    def _is_message_visible(self, message: ChatMessageContent, message_queue_count: int) -> bool:
        """Determine if a message is visible to the user."""
        return (
            not any(isinstance(item, (FunctionCallContent, FunctionResultContent)) for item in message.items)
            or message_queue_count == 0
        )

    @override
    async def receive(
        self,
        history: list[ChatMessageContent],
    ) -> None:
        """Receive the conversation messages.

        Do not include messages that only contain file references.

        Args:
            history: The history of messages in the conversation.
        """
        filtered_history: list[ChatMessageContent] = []
        for message in history:
            new_message = deepcopy(message)
            if new_message.items is None:
                new_message.items = []
            allowed_items = [item for item in new_message.items if isinstance(item, self.ALLOWED_CONTENT_TYPES)]
            if not allowed_items:
                continue
            new_message.items.clear()
            new_message.items.extend(allowed_items)
            filtered_history.append(new_message)
        self.messages.extend(filtered_history)

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

    @override
    async def reset(self) -> None:
        """Reset the channel state."""
        self.messages.clear()
