# Copyright (c) Microsoft. All rights reserved.

from collections.abc import AsyncIterable

from pydantic import Field

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.agent_channel import AgentChannel
from semantic_kernel.agents.chat_history_handler import ChatHistoryHandler
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class ChatHistoryChannel(AgentChannel):
    """An AgentChannel specialization for that acts upon a ChatHistoryHandler."""

    history: list[ChatMessageContent] = Field(default_factory=list, alias="history")

    def __init__(self) -> None:
        """Initialize the ChatHistoryChannel."""
        super().__init__()

    async def invoke(  # type: ignore
        self,
        agent: Agent,
    ) -> AsyncIterable[ChatMessageContent]:
        """Perform a discrete incremental interaction between a single Agent and AgentChat.

        Args:
            agent: The agent to interact with.

        Returns:
            An async iterable of ChatMessageContent.
        """
        if not isinstance(agent, ChatHistoryHandler):
            raise ValueError(f"Invalid channel binding for agent: {agent.id} ({type(agent).__name__})")

        async for message in agent.invoke(self.history):
            self.history.append(message)
            yield message

    async def receive(
        self,
        history: list[ChatMessageContent],
    ) -> None:
        """Receive the conversation messages.

        Args:
            history: The history of messages in the conversation.
        """
        self.history.extend(history)

    async def get_history(  # type: ignore
        self,
    ) -> AsyncIterable[ChatMessageContent]:
        """Retrieve the message history specific to this channel.

        Returns:
            An async iterable of ChatMessageContent.
        """
        for message in reversed(self.history):
            yield message
