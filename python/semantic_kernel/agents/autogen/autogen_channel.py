# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import TYPE_CHECKING, Any, AsyncIterable

from semantic_kernel.agents import Agent
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.contents.chat_message_content import ChatMessageContent

if TYPE_CHECKING:
    from autogen import ConversableAgent

logger: logging.Logger = logging.getLogger(__name__)


class AutoGenChannel(AgentChannel):
    """Minimal bridging channel between a Semantic Kernel conversation and an AutoGen ConversableAgent.

    We store conversation messages in memory
    and pass them to the underlying ConversableAgent as needed.
    """

    def __init__(self, conversable_agent: "ConversableAgent") -> None:
        """Initialize the AutoGenChannel."""
        pass

    async def receive(self, history: list[ChatMessageContent]) -> None:
        """Receive a message and store it in the local conversation buffer."""
        raise NotImplementedError("AutoGenChannel does not support receive.")

    def invoke(
        self,
        agent: "Agent",
        **kwargs: Any,
    ) -> AsyncIterable[tuple[bool, ChatMessageContent]]:
        """Invoke the agent with a single message."""
        raise NotImplementedError("AutoGenChannel does not support invoke.")

    def invoke_stream(
        self,
        agent: "Agent",
        messages: list["ChatMessageContent"],
        **kwargs,
    ) -> AsyncIterable["ChatMessageContent"]:
        """Invoke the agent with a stream of messages."""
        raise NotImplementedError("AutoGenChannel does not support streaming.")

    async def get_history(self) -> AsyncIterable["ChatMessageContent"]:
        """Return the conversation messages so far in reverse (latest first)."""
        raise NotImplementedError("AutoGenChannel does not support get_history.")

    async def reset(self) -> None:
        """Clear the local conversation buffer."""
        raise NotImplementedError("AutoGenChannel does not support reset.")
