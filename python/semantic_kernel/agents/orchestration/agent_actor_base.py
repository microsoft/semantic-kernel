# Copyright (c) Microsoft. All rights reserved.


import inspect
import sys
from collections.abc import Awaitable, Callable
from typing import Any

from semantic_kernel.agents.agent import Agent, AgentThread
from semantic_kernel.agents.orchestration.orchestration_base import DefaultTypeAlias
from semantic_kernel.agents.runtime.core.message_context import MessageContext
from semantic_kernel.agents.runtime.core.routed_agent import RoutedAgent
from semantic_kernel.contents.chat_history import ChatHistory

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover


class ActorBase(RoutedAgent):
    """A base class for actors running in the AgentRuntime."""

    @override
    async def on_message_impl(self, message: Any, ctx: MessageContext) -> Any | None:
        """Handle a message.

        Stop the handling of the message if the cancellation token is cancelled.
        """
        if ctx.cancellation_token.is_cancelled():
            return None

        return await super().on_message_impl(message, ctx)


class AgentActorBase(ActorBase):
    """A agent actor for multi-agent orchestration running on Agent runtime."""

    def __init__(
        self,
        agent: Agent,
        internal_topic_type: str,
        agent_response_callback: Callable[[DefaultTypeAlias], Awaitable[None] | None] | None = None,
    ) -> None:
        """Initialize the agent container.

        Args:
            agent (Agent): An agent to be run in the container.
            internal_topic_type (str): The topic type of the internal topic.
            agent_response_callback (Callable | None): A function that is called when a response is produced
                by the agents.
        """
        self._agent = agent
        self._internal_topic_type = internal_topic_type
        self._agent_response_callback = agent_response_callback

        self._agent_thread: AgentThread | None = None
        # Chat history to temporarily store messages before the agent thread is created
        self._chat_history = ChatHistory()

        ActorBase.__init__(self, description=agent.description or "Semantic Kernel Agent")

    async def _call_agent_response_callback(self, message: DefaultTypeAlias) -> None:
        """Call the agent_response_callback function if it is set.

        Args:
            message (DefaultTypeAlias): The message to be sent to the agent_response_callback.
        """
        # TODO(@taochen): Support streaming
        if self._agent_response_callback:
            if inspect.iscoroutinefunction(self._agent_response_callback):
                await self._agent_response_callback(message)
            else:
                self._agent_response_callback(message)
