# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from typing import TYPE_CHECKING, Any, AsyncIterable

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from semantic_kernel.agents import Agent
from semantic_kernel.agents.channels.agent_channel import AgentChannel
from semantic_kernel.contents.chat_message_content import ChatMessageContent

if TYPE_CHECKING:
    from autogen import ConversableAgent

logger: logging.Logger = logging.getLogger(__name__)


class AutoGenConversableAgentChannel(AgentChannel):
    """Minimal bridging channel between a Semantic Kernel conversation and an AutoGen ConversableAgent.

    We store conversation messages in memory
    and pass them to the underlying ConversableAgent as needed.
    """

    def __init__(self, conversable_agent: "ConversableAgent") -> None:
        """Initialize the AutoGenConversableAgent Channel."""
        pass

    @override
    async def receive(self, history: list[ChatMessageContent]) -> None:
        """Receive a message and store it in the local conversation buffer."""
        raise NotImplementedError("AutoGenConversableAgent Channel does not support receive.")

    @override
    def invoke(
        self,
        agent: "Agent",
        **kwargs: Any,
    ) -> AsyncIterable[tuple[bool, ChatMessageContent]]:
        """Invoke the agent with a single message."""
        raise NotImplementedError("AutoGenConversableAgent Channel does not support invoke.")

    @override
    def invoke_stream(
        self,
        agent: "Agent",
        messages: list["ChatMessageContent"],
        **kwargs,
    ) -> AsyncIterable["ChatMessageContent"]:
        """Invoke the agent with a stream of messages."""
        raise NotImplementedError("AutoGenConversableAgent Channel does not support streaming.")

    @override
    async def get_history(self) -> AsyncIterable[ChatMessageContent]:  # type: ignore
        """Return the conversation messages so far in reverse (latest first)."""
        raise NotImplementedError("AutoGenConversableAgent Channel does not support get_history.")

    @override
    async def reset(self) -> None:
        """Clear the local conversation buffer."""
        raise NotImplementedError("AutoGenConversableAgent Channel does not support reset.")
